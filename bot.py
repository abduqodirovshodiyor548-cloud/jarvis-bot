"""Jarvis - Registon maktabi marketing yordamchisi (Telegram bot).

Barcha maxfiy qiymatlar faqat muhit o'zgaruvchilaridan (env) o'qiladi:
  TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_USER_IDS, CLAUDE_MODEL
  WEBHOOK_URL (ixtiyoriy; Render'da RENDER_EXTERNAL_URL avtomatik ishlatiladi)
"""
import hashlib
import logging
import os
from collections import defaultdict, deque

from anthropic import AsyncAnthropic
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # so'rov URL'larida token bor, logga chiqmasin
log = logging.getLogger("jarvis")

def _env(name: str) -> str:
    value = os.environ.get(name, "").strip().strip('"').strip("'")
    if not value:
        raise SystemExit(f"XATO: {name} muhit o'zgaruvchisi kiritilmagan (Render -> Environment).")
    return value


TOKEN = _env("TELEGRAM_BOT_TOKEN")
os.environ["ANTHROPIC_API_KEY"] = _env("ANTHROPIC_API_KEY")
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
ALLOWED = {int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x}
HISTORY_LEN = 20  # har bir chat uchun eslab qolinadigan oxirgi xabarlar soni

SYSTEM_PROMPT = """Sen Jarvis - Shodiyorning marketing yordamchisisan.
Shodiyor Registon maktabida (xususiy maktab) marketing bilan shug'ullanadi va marketing konsalting qiladi.
Targetolog sherigi - Muzaffar. Qabul mavsumlari: 1-mavsum 1200 o'quvchi, rekord mavsum 1800 o'quvchi.
Maktab dushanbadan shanbagacha ishlaydi.

Qoidalar:
- Har doim lotin yozuvidagi o'zbek tilida javob ber, "Shodiyor" deb murojaat qil.
- Qisqa va aniq: avval natija, keyin izoh. Maqtov uchun maqtama, xato ko'rsang ochiq ayt.
- Raqam o'ylab topma: ma'lumot bo'lmasa so'ra yoki "taxminiy" deb belgila.
- Ota-onalarni chalg'itadigan yoki tekshirib bo'lmaydigan da'volar yozma ("eng yaxshi maktab" kabi bo'sh va'dalar emas, aniq faktlar).

Video ssenariy: platforma, davomiylik, maqsad, kim gapirishini aniqla (aytilmasa o'zing taklif qil).
Ssenariyni ustunlar bilan ber: vaqt | kadrda nima | ovoz matni | ekrandagi yozuv.
Birinchi 3 soniyada ota-onaning real tashvishidan ilmoq; oxirida aniq chaqiruv (qo'ng'iroq, Telegram bot, ro'yxatdan o'tish).
So'ralmasa ham 2-3 xil ilmoq varianti taklif qil.

Post va reklama matni: 3 variant - muammo-yechim, natija va raqamlar, ota-ona hikoyasi. Birinchi qator - ilmoq.

Tahlil: CPL, lid -> qabul konversiyasi, CAC, kanallar bo'yicha taqqoslash.
Tuzilma: asosiy xulosa 2-3 gapda; nima ishlayapti va nima ishlamayapti; keyingi haftaga 3 ta aniq harakat.

Telegram'da o'qish qulay bo'lsin: jadval o'rniga raqamlangan bandlar ishlat, markdown belgilarini (**, ##) ishlatma."""

client = AsyncAnthropic()  # ANTHROPIC_API_KEY env'dan o'qiladi
history: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_LEN))


async def allowed(update: Update) -> bool:
    uid = update.effective_user.id
    if not ALLOWED:
        await update.message.reply_text(
            f"Sizning Telegram ID: {uid}\nUni ALLOWED_USER_IDS ga yozing va botni qayta ishga tushiring."
        )
        return False
    if uid not in ALLOWED:
        log.warning("Ruxsatsiz urinish: user_id=%s", uid)
        await update.message.reply_text("Kechirasiz, bu bot shaxsiy.")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await allowed(update):
        await update.message.reply_text(
            "Salom, Shodiyor! Men Jarvisman. Ssenariy, post, reklama matni yoki tahlil - nima kerak?\n"
            "/new - suhbatni yangidan boshlash"
        )


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await allowed(update):
        history.pop(update.effective_chat.id, None)
        await update.message.reply_text("Yangi suhbat boshlandi.")


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return
    chat_id = update.effective_chat.id
    msgs = history[chat_id]
    msgs.append({"role": "user", "content": update.message.text})
    await context.bot.send_chat_action(chat_id, ChatAction.TYPING)

    # Tarix deque bilan qirqilganda birinchi xabar "user" bo'lishi shart
    convo = list(msgs)
    while convo and convo[0]["role"] != "user":
        convo.pop(0)

    try:
        resp = await client.messages.create(
            model=MODEL, max_tokens=4000, system=SYSTEM_PROMPT, messages=convo
        )
        answer = "".join(b.text for b in resp.content if b.type == "text").strip() or "(bo'sh javob)"
    except Exception:
        log.exception("Claude API xatosi")
        msgs.pop()
        await update.message.reply_text("Xatolik yuz berdi, birozdan keyin qayta urinib ko'ring.")
        return

    msgs.append({"role": "assistant", "content": answer})
    for i in range(0, len(answer), 4000):  # Telegram cheklovi 4096 belgi
        await update.message.reply_text(answer[i : i + 4000])


def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    log.info("Jarvis ishga tushdi (model: %s)", MODEL)

    # Render bepul Web Service'da RENDER_EXTERNAL_URL avtomatik beriladi -> webhook rejimi.
    # Server uxlab qolsa, Telegram'dan kelgan xabar uni uyg'otadi.
    public_url = os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL")
    if public_url:
        path = hashlib.sha256(TOKEN.encode()).hexdigest()[:32]  # tokenni URL'da ochmaslik uchun
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", "10000")),
            url_path=path,
            webhook_url=f"{public_url.rstrip('/')}/{path}",
            secret_token=path,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
