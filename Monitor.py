import os
import json
import asyncio
from threading import Thread
from flask import Flask
from telethon import TelegramClient, events

# ==============================
# CONFIG (ISI DI REPLIT SECRETS)
# ==============================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = "session"

EXCLUDED_GROUP = "Project & IT Support BSS"
DATA_FILE = "data.json"

# ==============================
# DEFAULT DATA
# ==============================
default_data = {
    "keywords": ["error", "teknisi", "down", "offline"],
    "monitoring": True,
    "forward_to": None
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ==============================
# FLASK SERVER (UPTIME ROBOT)
# ==============================
app = Flask("")

@app.route("/")
def home():
    return "BOT RUNNING"

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

# ==============================
# TELEGRAM CLIENT
# ==============================
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ==============================
# DEBUG MONITOR
# ==============================
@client.on(events.NewMessage(outgoing=True))
async def debug_log(event):
    print("Outgoing detected:", event.raw_text)

# ==============================
# MONITORING
# ==============================
@client.on(events.NewMessage(incoming=True))
async def monitor_handler(event):

    if not data["monitoring"]:
        return

    if not event.is_group:
        return

    chat = await event.get_chat()
    group_name = (getattr(chat, "title", "") or "").lower()

    if EXCLUDED_GROUP.lower() in group_name:
        return

    text = event.raw_text.lower()

    for word in data["keywords"]:
        if word.lower() in text:
            print(f"Keyword detected: {word}")
            if data["forward_to"]:
                await client.forward_messages(
                    data["forward_to"],
                    event.message
                )
            break

# ==============================
# COMMANDS (USERBOT)
# ==============================

@client.on(events.NewMessage(outgoing=True, pattern=r"\.ping"))
async def ping_cmd(event):
    await event.reply("Pong 🏓")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.help"))
async def help_cmd(event):
    await event.reply("""
🔥 COMMAND LIST 🔥

.monitor on/off
.add <keyword>
.del <keyword>
.list
.clear
.setforward (reply pesan target)
.stopforward
.status
""")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.monitor (on|off)"))
async def monitor_cmd(event):
    state = event.pattern_match.group(1)
    data["monitoring"] = True if state == "on" else False
    save_data(data)
    await event.reply(f"Monitoring {state.upper()}")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.add (.+)"))
async def add_cmd(event):
    word = event.pattern_match.group(1)
    if word not in data["keywords"]:
        data["keywords"].append(word)
        save_data(data)
    await event.reply(f"Keyword ditambahkan: {word}")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.del (.+)"))
async def del_cmd(event):
    word = event.pattern_match.group(1)
    if word in data["keywords"]:
        data["keywords"].remove(word)
        save_data(data)
    await event.reply(f"Keyword dihapus: {word}")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.list"))
async def list_cmd(event):
    await event.reply("Keyword aktif:\n" + "\n".join(data["keywords"]))

@client.on(events.NewMessage(outgoing=True, pattern=r"\.clear"))
async def clear_cmd(event):
    data["keywords"] = []
    save_data(data)
    await event.reply("Semua keyword dihapus.")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.setforward"))
async def set_forward(event):
    if not event.is_reply:
        await event.reply("Reply pesan dari grup tujuan.")
        return

    replied = await event.get_reply_message()
    data["forward_to"] = replied.chat_id
    save_data(data)
    await event.reply("Grup tujuan diset.")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.stopforward"))
async def stop_forward(event):
    data["forward_to"] = None
    save_data(data)
    await event.reply("Forward dimatikan.")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.status"))
async def status_cmd(event):
    await event.reply(f"""
Monitoring: {data['monitoring']}
Keyword: {len(data['keywords'])}
Forward Active: {data['forward_to'] is not None}
Excluded: {EXCLUDED_GROUP}
""")

# ==============================
# MAIN LOOP
# ==============================
async def main():
    await client.start()
    print("Telegram Connected")
    me = await client.get_me()
    print("Login sebagai:", me.username)
    await client.run_until_disconnected()

asyncio.run(main())
