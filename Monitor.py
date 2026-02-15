import os
import asyncio
import threading
from datetime import datetime, timedelta

from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ===== REPLIT SECRETS (WAJIB ADA) =====
# TELEGRAM_API_ID         = angka api_id
# TELEGRAM_API_HASH       = api_hash
# TELEGRAM_STRING_SESSION = string session panjang
api_id = int(os.environ["TELEGRAM_API_ID"])
api_hash = os.environ["TELEGRAM_API_HASH"]
string_session = os.environ["TELEGRAM_STRING_SESSION"]

# Grup khusus untuk kumpulin alert
TARGET = "@errorgais"

# Keyword yang dipantau
KEYWORDS = [
    "error", "kendala", "offline", "down", "gagal", "rusak",
    "problem", "gangguan", "teknisi"
]

# Anti spam (0 = matiin)
COOLDOWN_SECONDS_PER_CHAT = 1
_last_alert_time = {}

# Anti panjang (Telegram limit)
MAX_SNIPPET = 700

# ===== WEB SERVER untuk UptimeRobot =====
app = Flask(__name__)

@app.route("/")
def home():
    return "OK"  # ini yang bikin UptimeRobot gak 404

@app.route("/health")
def health():
    return "alive"

def run_web():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

# Start web server di thread lain
threading.Thread(target=run_web, daemon=True).start()


def hit_keyword(text: str):
    t = (text or "").lower()
    for k in KEYWORDS:
        if k in t:
            return k
    return None


async def main():
    async with TelegramClient(StringSession(string_session), api_id, api_hash) as client:
        print(f"Monitoring aktif... target: {TARGET}")

        @client.on(events.NewMessage)
        async def handler(event):
            if not (event.is_group or event.is_channel):
                return

            raw = event.raw_text or ""
            matched = hit_keyword(raw)
            if not matched:
                return

            now = datetime.now()
            chat_id = event.chat_id

            # cooldown per chat
            if COOLDOWN_SECONDS_PER_CHAT > 0:
                last = _last_alert_time.get(chat_id)
                if last and (now - last) < timedelta(seconds=COOLDOWN_SECONDS_PER_CHAT):
                    return
                _last_alert_time[chat_id] = now

            # ambil info chat & sender (aman)
            try:
                chat = await event.get_chat()
            except Exception:
                chat = None
            try:
                sender = await event.get_sender()
            except Exception:
                sender = None

            group_name = getattr(chat, "title", None) or getattr(chat, "username", None) or str(chat_id)
            sender_name = getattr(sender, "first_name", None) or getattr(sender, "username", None) or str(event.sender_id)

            waktu = now.strftime("%d-%m-%Y %H:%M:%S")

            snippet = raw.replace("\n", " ").strip()
            if len(snippet) > MAX_SNIPPET:
                snippet = snippet[:MAX_SNIPPET] + "…"

            teks = (
                f"🚨 ALERT: {matched}\n"
                f"Waktu: {waktu}\n"
                f"Grup asal: {group_name}\n"
                f"Dari: {sender_name}\n\n"
                f"Pesan (ringkas):\n{snippet}"
            )

            # Kirim alert ke grup monitoring
            try:
                await client.send_message(TARGET, teks)
            except FloodWaitError as e:
                print(f"FloodWait {e.seconds}s, nunggu...")
                await asyncio.sleep(e.seconds)
                await client.send_message(TARGET, teks)
            except Exception as e:
                print("Gagal kirim alert:", repr(e))

        await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
