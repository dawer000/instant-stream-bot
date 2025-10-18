import os
import threading
from flask import Flask
from pyrogram import Client, filters

# === Telegram Config ===
API_ID = 22121081
API_HASH = "40aa45abc830f38901ac455674812256"
BOT_TOKEN = "8425638442:AAFdXiLbKuN57hM4krrbIf0AT8OqJY0Pe3o"

# === Cloudflare Worker URL ===
WORKER_URL = "https://moviestream.dawerraza068.workers.dev"

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Telegram Bot Handler ---
@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"

    # Construct instant Worker link
    stream_url = f"{WORKER_URL}/stream/{file_id}"

    # Reply to user
    await message.reply_text(
        f"🎬 **Your Instant Stream Link is Ready!**\n\n"
        f"📁 `{file_name}`\n"
        f"🌐 Watch instantly:\n👉 {stream_url}",
        disable_web_page_preview=True
    )

# --- Flask Endpoint for Testing ---
@app.route("/")
def home():
    return "✅ Instant Telegram Stream Bot Running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

if __name__ == "__main__":
    # Run Flask in a thread
    threading.Thread(target=run_flask).start()
    # Run Telegram bot
    bot.run()
