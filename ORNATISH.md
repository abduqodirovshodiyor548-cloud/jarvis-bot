# Jarvis Telegram botini o'rnatish

Fayllar: `bot.py` (bot kodi), `requirements.txt` (kutubxonalar), `.env.example` (sozlamalar namunasi).

## 0. Avval xavfsizlik: tokenni yangilang
Token chatga yozilgan, shuning uchun uni yangilash tavsiya etiladi:
1. Telegram'da @BotFather'ni oching -> `/mybots` -> botingizni tanlang.
2. `API Token` -> `Revoke current token`. Yangi token chiqadi.
3. Yangi tokenni hech qayerga yozmang, faqat 3-qadamdagi serverga kiriting.

## 1. Anthropic API kalitini olish
1. https://console.anthropic.com ga kiring (Google akkaunt bilan bo'ladi).
2. `Billing` bo'limida karta ulang va balansni to'ldiring (boshlash uchun 5-10 $ yetadi).
3. `API Keys` -> `Create Key`. `sk-ant-...` bilan boshlanadigan kalitni nusxalang (faqat bir marta ko'rsatiladi).
4. Tavsiya: `Limits` bo'limida oylik xarajat chegarasini qo'ying.

Narx: har bir so'rov bo'yicha to'lanadi. Aniq narxni console'dagi `Usage` bo'limida kuzatib boring.

## 2. Server tanlash
Bot doim yoqiq turishi kerak, shuning uchun kompyuter emas, server kerak. Ikki variant:

| Variant | Qulayligi | Narxi (taxminiy) |
|---|---|---|
| **Railway** (tavsiya) | Kod yozmasdan, brauzer orqali | ~5 $/oy |
| VPS (Hetzner, DigitalOcean, mahalliy hosting) | Terminal bilan ishlash kerak | ~4-6 $/oy |

Narxlar o'zgarishi mumkin, saytlarida tekshiring.

## 3a. Railway orqali ishga tushirish (oson yo'l)
1. https://github.com da yangi **private** repozitoriy oching va `bot.py`, `requirements.txt` fayllarini yuklang (`.env` faylini yuklamang).
2. https://railway.app ga GitHub bilan kiring -> `New Project` -> `Deploy from GitHub repo` -> repozitoriyni tanlang.
3. Loyiha ichida `Variables` bo'limiga quyidagilarni qo'shing:
   - `TELEGRAM_BOT_TOKEN` = BotFather bergan yangi token
   - `ANTHROPIC_API_KEY` = `sk-ant-...` kalit
   - `ALLOWED_USER_IDS` = hozircha bo'sh qoldiring
4. Start buyrug'i `Procfile` ichida bor, alohida sozlash shart emas.
5. Deploy tugagach, Telegram'da botga `/start` yozing. Bot sizning **ID raqamingizni** aytadi.
6. Shu raqamni `ALLOWED_USER_IDS` ga yozing (bir nechta odam bo'lsa vergul bilan: `123,456`). Railway botni o'zi qayta ishga tushiradi.
7. Yana `/start` yozing: "Salom, Shodiyor!" chiqsa, tayyor.

## 3b. VPS orqali ishga tushirish (Ubuntu)
```bash
sudo apt update && sudo apt install -y python3-venv
mkdir ~/jarvis && cd ~/jarvis        # bot.py va requirements.txt ni shu yerga yuklang
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env    # qiymatlarni to'ldiring
chmod 600 .env
```
Doim ishlashi uchun `/etc/systemd/system/jarvis.service` fayli:
```ini
[Unit]
Description=Jarvis Telegram bot
After=network-online.target

[Service]
WorkingDirectory=/root/jarvis
EnvironmentFile=/root/jarvis/.env
ExecStart=/root/jarvis/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now jarvis
journalctl -u jarvis -f              # loglarni ko'rish
```
ID olish va cheklov qo'yish 3a dagi 5-7 qadamlar bilan bir xil (`.env` ni o'zgartirgach: `sudo systemctl restart jarvis`).

## Bot qanday ishlaydi
- Faqat `ALLOWED_USER_IDS` dagi odamlar ishlata oladi, boshqalarga "bu bot shaxsiy" deydi.
- Oxirgi 20 ta xabarni eslab qoladi. `/new` - suhbatni tozalash. Server qayta ishga tushsa, tarix o'chadi.
- Hozircha faqat matn bilan ishlaydi (rasm, ovoz, fayl yo'q).
- Model: `claude-sonnet-5-5`. Arzonroq kerak bo'lsa `CLAUDE_MODEL=claude-haiku-5-5`, kuchliroq kerak bo'lsa `claude-opus-5-5`.
