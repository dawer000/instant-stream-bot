import os
from flask import Flask, Response, stream_with_context
from pyrogram import Client

# Environment Variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH"))
BOT_TOKEN = os.environ.get("BOT_TOKEN")

BASE_URL = os.environ.get("BASE_URL")

app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.route("/")
def home():
    return "✅ Instant Telegram Stream Bot Running!"

@app.route("/stream/<file_id>")
def stream(file_id):
    @stream_with_context
    def generate():
        try:
            # Stream media in 1MB chunks
            for chunk in bot.stream_media(file_id, block_size=1024*1024):
                yield chunk
        except Exception as e:
            print(f"❌ Stream Error: {e}")

    return Response(generate(), mimetype="video/mp4")
