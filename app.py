import os
from pyrogram import Client, filters

# === Telegram Config ===
API_ID = int(os.environ.get("API_ID", "22121081"))
API_HASH = os.environ.get("API_HASH", "40aa45abc830f38901ac455674812256")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8425638442:AAFwGADH9rrv-Ov8Kv8dWk4CvHv8t8lUxi8")

# === Cloudflare Worker BASE_URL ===
BASE_URL = os.environ.get(
    "BASE_URL", "https://moviestream.dawerraza068.workers.dev"
)

# === Initialize Pyrogram Bot ===
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# --- Handle media messages ---
@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"

    # Generate instant stream link via Cloudflare Worker
    stream_url = f"{BASE_URL}/stream/{file_id}"

    await message.reply_text(
        f"🎬 **Your Stream is Ready!**\n\n"
        f"📁 `{file_name}`\n"
        f"🌐 Stream instantly here:\n👉 {stream_url}",
        disable_web_page_preview=True
    )


# --- Run Bot ---
if __name__ == "__main__":
    print("🚀 Instant Stream Bot running with Cloudflare Worker!")
    bot.run()
