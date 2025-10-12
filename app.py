import os
from flask import Flask, request, Response
from pyrogram import Client, filters
import asyncio

# === Telegram Config from Environment Variables ===
API_ID = int(os.environ.get("API_ID", 22121081))
API_HASH = os.environ.get("API_HASH", "40aa45abc830f38901ac455674812256")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8425638442:AAFwGADH9rrv-Ov8Kv8dWk4CvHv8t8lUxi8")
BASE_URL = os.environ.get("BASE_URL", "https://your-railway-url.up.railway.app")

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.route("/")
def home():
    return "✅ Instant Telegram Stream Bot Running!"


# --- Handle media messages ---
@bot.on_message(filters.video | filters.document)
def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"

    # Generate instant stream link using BASE_URL
    stream_url = f"{BASE_URL}/stream/{file_id}"
    message.reply_text(
        f"🎬 **Your Stream is Ready!**\n\n"
        f"📁 `{file_name}`\n"
        f"🌐 Stream instantly here:\n👉 {stream_url}",
        disable_web_page_preview=True
    )


# --- Stream endpoint ---
@app.route("/stream/<file_id>")
def stream(file_id):
    range_header = request.headers.get("Range", None)

    def generate():
        try:
            # Stream directly from Telegram in chunks
            for chunk in bot.stream_media(file_id):
                yield chunk
        except Exception as e:
            print(f"❌ Stream Error: {e}")

    return Response(generate(), mimetype="video/mp4")


# === Run Flask using PORT from Railway ===
def run_flask():
    port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)



if __name__ == "__main__":
    # Run Flask + Pyrogram in asyncio loop
    import threading
    threading.Thread(target=run_flask).start()
    bot.run()
