import os
import asyncio
from flask import Flask, request, Response, stream_with_context
from pyrogram import Client, filters

# === Telegram Config from Environment Variables ===
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.route("/")
def home():
    return "✅ Instant Telegram Stream Bot Running!"


# --- Handle media messages ---
@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"

    # Use BASE_URL for proper streaming
    stream_url = f"{BASE_URL}/stream/{file_id}"
    await message.reply_text(
        f"🎬 **Your Stream is Ready!**\n\n"
        f"📁 `{file_name}`\n"
        f"🌐 Stream instantly here:\n👉 {stream_url}",
        disable_web_page_preview=True
    )


# --- Stream endpoint ---
@app.route("/stream/<file_id>")
def stream(file_id):
    @stream_with_context
    def generate():
        try:
            # Download media in chunks from Telegram and yield to client
            for chunk in bot.stream_media(file_id, block_size=1024*1024):  # 1MB chunks
                yield chunk
        except Exception as e:
            print(f"❌ Stream Error: {e}")

    return Response(generate(), mimetype="video/mp4")


# === Run Flask using PORT from Railway ===
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    # Run Flask in separate thread
    from threading import Thread
    Thread(target=run_flask).start()

    # Run Pyrogram bot async
    asyncio.run(bot.start())
    print("🚀 Bot Running")
    asyncio.get_event_loop().run_forever()
