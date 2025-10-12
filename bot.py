import os
import asyncio
from pyrogram import Client, filters

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")

bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"

    stream_url = f"{BASE_URL}/stream/{file_id}"
    await message.reply_text(
        f"🎬 **Your Stream is Ready!**\n\n"
        f"📁 `{file_name}`\n"
        f"🌐 Stream instantly here:\n👉 {stream_url}",
        disable_web_page_preview=True
    )

if __name__ == "__main__":
    asyncio.run(bot.start())
    asyncio.get_event_loop().run_forever()
