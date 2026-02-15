import asyncio
import threading
from flask import Flask
from datetime import datetime, timedelta

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

@app.get("/")
def home():
    return "Telegram monitor alive"
def run_web():
    app.run(host="0.0.0.0", port=3000)
threading.Thread(target=run_web, daemon=True).start()

# ====== ISI INI ======
api_id = 32737298  # GANTI
api_hash = "6034b051b2d37e7ba255ea8c3ab5a608"
string_session = "1BVtsOLYBu1tymV0KEAeh6n0jI8eTm9lh_gG2GtCnoRedvS_jlq8u6x7Wwy31K8D1scZWea-L8EaaHqhrfRRQhbWE62QlYPzHDlz2Z8VIpZfGBHq57SuqhZoVTywOvUFvTgyUcBbB7sXXjj0el222i1S_HUKFuB5NWJSGujU1MufiTNOay3K4k3WNS4YkDa-5PoBWYnjDKB0VjlCb2F7laxKg1LvSTvhxlgDgm6-fhtt0YgyBS5sEGDGDTmO-f5oy6-7lnpKmiTw4OnksfsA_lK060hVOlS9NTNet5bNDjhWWtE3RZKA4BTdTKlmWqkM0ELtGMK4tgnr3XDNIyGXeD0Glgfh0Epc="
TARGET = "@errorgais"
# =====================

KEYWORDS = ["error", "kendala", "offline", "down", "gagal", "rusak", "teknisi", "gangguan", "teknisi"]

# Anti spam: set 0 kalau mau tanpa cooldown
COOLDOWN_SECONDS_PER_CHAT = 0
_last_alert_time = {}

# Maks panjang teks alert (biar gak mentok limit Telegram)
MAX_SNIPPET = 700

def hit_keyword(text: str):
    t = (text or "").lower()
    for k in KEYWORDS:
        if k in t:
            return k
    return None

def build_tme_link(chat_id: int, msg_id: int):
    # Link hanya valid untuk supergroup/channel: t.me/c/<id tanpa -100>/<msg_id>
    # Kalau bukan supergroup, bisa gagal — jadi kita fallback.
    if chat_id and str(chat_id).startswith("-100"):
        cid = str(chat_id)[4:]  # hapus "-100"
        return f"https://t.me/c/{cid}/{msg_id}"
    return None

async def main():
    async with TelegramClient(StringSession(string_session), api_id, api_hash) as client:
        print("Monitoring aktif... target:", TARGET)

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

            # ambil chat & sender (ini kadang agak lambat, jadi cuma dilakukan kalau match)
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

            link = build_tme_link(chat_id, event.id)
            link_line = f"\nLink pesan: {link}" if link else ""

            teks = (
                f"🚨 CEK GRUP SO: {matched}\n"
                f"Waktu: {waktu}\n"
                f"Grup asal: {group_name}\n"
                f"Dari: {sender_name}\n"
                f"{link_line}\n\n"
                f"Pesan (ringkas):\n{snippet}"
            )

            # kirim ke grup khusus error (tanpa markdown biar anti parse error)
            try:
                await client.send_message(TARGET, teks)
            except FloodWaitError as e:
                print(f"FloodWait {e.seconds}s, nunggu...")
                await asyncio.sleep(e.seconds)
                await client.send_message(TARGET, teks)
            except Exception as e:
                print("Gagal kirim ke TARGET:", repr(e))

        await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

