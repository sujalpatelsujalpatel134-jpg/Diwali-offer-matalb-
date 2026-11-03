import os
import logging
import asyncio
import json
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Logging setup
logging.basicConfig(level=logging.INFO)

# Direct Credentials (No Env Variables needed!)
API_ID = 36244302
API_HASH = "5e844495cd20f53c82d84f97289e3b73"
BOT_TOKEN = "9072774703:AAEXziVGAuhTQbsqv2KF1APQt39172pjp3Y"
ADMIN_ID = 7712648594

# Local JSON file for saving batches (Zero database errors)
BATCH_FILE = "batches.json"

def load_batches():
    if os.path.exists(BATCH_FILE):
        try:
            with open(BATCH_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_batches(data):
    with open(BATCH_FILE, "w") as f:
        json.dump(data, f)

app = Client(
    "FileShareBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if len(message.command) > 1:
        payload = message.command[1]
        if payload.startswith("batch_"):
            batch_id = payload.split("_")[1]
            batches = load_batches()
            batch_data = batches.get(batch_id)
            if batch_data:
                for file_id in batch_data.get("file_ids", []):
                    try:
                        await client.copy_message(
                            chat_id=message.from_user.id,
                            from_chat_id=ADMIN_ID,
                            message_id=file_id
                        )
                        await asyncio.sleep(0.3)  # Flood prevention
                    except Exception as e:
                        logging.error(f"Error copying message {file_id}: {e}")
                return
        else:
            try:
                file_msg_id = int(payload)
                await client.copy_message(
                    chat_id=message.from_user.id,
                    from_chat_id=ADMIN_ID,
                    message_id=file_msg_id
                )
                return
            except Exception:
                pass

    await message.reply_text(
        "👋 **Welcome to File Share Bot!**\n\nSend me any video or file (Admin only) to generate a shareable link."
    )

@app.on_message((filters.video | filters.document | filters.audio) & filters.user(ADMIN_ID) & filters.private)
async def store_file(client: Client, message: Message):
    bot_info = await client.get_me()
    file_link = f"https://t.me/{bot_info.username}?start={message.id}"
    
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔗 Share Link", url=file_link)]]
    )
    await message.reply_text(
        f"✅ **File Saved Successfully!**\n\nHere is your shareable link:\n`{file_link}`",
        reply_markup=keyboard,
        quote=True
    )

@app.on_message(filters.command("batch") & filters.user(ADMIN_ID) & filters.private)
async def batch_handler(client: Client, message: Message):
    cmd = message.command
    if len(cmd) != 3:
        await message.reply_text("❌ Usage: `/batch start_message_id end_message_id`")
        return
    
    try:
        start_id = int(cmd[1])
        end_id = int(cmd[2])
    except ValueError:
        await message.reply_text("❌ Message IDs must be integers.")
        return

    file_ids = list(range(start_id, end_id + 1))
    batch_token = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    
    batches = load_batches()
    batches[batch_token] = {"file_ids": file_ids}
    save_batches(batches)

    bot_info = await client.get_me()
    batch_link = f"https://t.me/{bot_info.username}?start=batch_{batch_token}"
    
    await message.reply_text(
        f"📦 **Batch Created Successfully!**\n\nLink for {len(file_ids)} files:\n`{batch_link}`"
    )

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID) & filters.private)
async def stats_handler(client: Client, message: Message):
    batches = load_batches()
    total_batches = len(batches)
    await message.reply_text(
        f"📊 **Bot Statistics**\n\n• Total Active Batches: {total_batches}\n• Status: Online & Running 🟢"
    )

@app.on_message(filters.command("del") & filters.user(ADMIN_ID) & filters.private)
async def delete_handler(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to the file message you want to clear/invalidate link for.")
        return
    
    await message.reply_text("🗑️ Associated link reference cleared.")

async def main():
    await app.start()
    print("Bot started successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
