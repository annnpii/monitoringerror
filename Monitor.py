import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]
string_session = os.environ["STRING_SESSION"]

keywords = ["error", "kendala", "teknisi", "gagal", "rusak"]

async def main():
    async with TelegramClient(StringSession(string_session), api_id, api_hash) as client:

        @client.on(events.NewMessage)
        async def handler(event):
            if event.is_group:
                message = event.raw_text.lower()

                if any(word in message for word in keywords):

                    chat = await event.get_chat()
                    sender = await event.get_sender()
                    waktu = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

                    group_name = chat.title if chat else "Unknown Group"
                    sender_name = sender.first_name if sender else "Unknown"

                    await client.send_message(
                        "me",
                        f"🚨 ERROR TERDETEKSI 🚨\n\n"
                        f"Waktu: {waktu}\n"
                        f"Grup: {group_name}\n"
                        f"Dari: {sender_name}\n"
                        f"Pesan: {event.raw_text}"
                    )

        print("Monitoring aktif (Cloud Mode)...")
        await client.run_until_disconnected()

asyncio.run(main())