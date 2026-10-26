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

Bu balans bot ishlashi uchun shart: botning har bir javobi shu balansdan to'lanadi. Aniq narxni console'dagi `Usage` bo'limida kuzatib boring.

## 2. Server: Render bepul tarifi
Bot Render'ning **bepul Web Service** tarifida ishlaydi (karta shart emas). 15 daqiqa jim tursa server uxlaydi, lekin sizning xabaringiz uni uyg'otadi. Uxlagandan keyingi birinchi javob 30-60 soniya kechikishi mumkin, keyingilari odatdagidek tez.

## 3a. Render orqali ishga tushirish
1. https://render.com ga `GitHub` tugmasi bilan kiring.
2. `New +` -> **`Web Service`** -> `jarvis-bot` repozitoriysini tanlang (ro'yxatda bo'lmasa, `Configure account` orqali GitHub'dan ruxsat bering).
3. Sozlamalar:
   - Language: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
   - Instance Type: **`Free`**
4. `Environment Variables` bo'limiga qo'shing:
   - `TELEGRAM_BOT_TOKEN` = BotFather bergan yangi token
   - `ANTHROPIC_API_KEY` = `sk-ant-...` kalit
   - `ALLOWED_USER_IDS` = hozircha bo'sh qoldiring
5. `Deploy Web Service` ni bosing. Logda "Jarvis ishga tushdi" chiqishini kuting (2-4 daqiqa).
6. Telegram'da botga `/start` yozing. Bot sizning **ID raqamingizni** aytadi.
7. Shu raqamni Render'da `Environment` bo'limida `ALLOWED_USER_IDS` ga yozing (bir nechta odam bo'lsa vergul bilan: `123,456`) va saqlang. Render botni qayta ishga tushiradi.
8. Yana `/start` yozing: "Salom, Shodiyor!" chiqsa, tayyor.

Xarajat: faqat Anthropic API balansi (har bir javob uchun ozgina yechiladi). Render bepul.

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
ID olish va cheklov qo'yish 3a dagi 6-8 qadamlar bilan bir xil (`.env` ni o'zgartirgach: `sudo systemctl restart jarvis`).

## Bot qanday ishlaydi
- Faqat `ALLOWED_USER_IDS` dagi odamlar ishlata oladi, boshqalarga "bu bot shaxsiy" deydi.
- Oxirgi 20 ta xabarni eslab qoladi. `/new` - suhbatni tozalash. Server uxlasa yoki qayta ishga tushsa, tarix o'chadi.
- Fayl yoki papkani ZIP qilib yuborsangiz (PDF, DOCX, XLSX, TXT, CSV, MD, 20 MB gacha), Anthropic serverida saqlaydi va savollarga shu fayllardan javob beradi. Server uxlasa ham fayllar o'chmaydi.
- `/fayllar` - saqlangan fayllar ro'yxati, `/ochir 2` - 2-faylni o'chirish.
- Diqqat: har bir savolda barcha fayllar modelga qayta yuboriladi. Fayl qancha ko'p va katta bo'lsa, javob shuncha qimmatlashadi. Keraksiz fayllarni o'chirib turing.
- Ovozli xabarni tushunadi, agar Render'da `GROQ_API_KEY` bo'lsa (kalit: https://console.groq.com -> `API Keys` -> `Create API Key`, bepul tarif). Bot avval "Eshitdim: ..." deb matnni ko'rsatadi, keyin javob beradi.
- Rasmni hozircha tushunmaydi.
- Model: `claude-sonnet-5-5`. Arzonroq kerak bo'lsa `CLAUDE_MODEL=claude-haiku-5-5`, kuchliroq kerak bo'lsa `claude-opus-5-5`.
