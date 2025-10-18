import os
import threading
from flask import Flask, request
from pyrogram import Client, filters
import subprocess

# === Telegram User Account Config ===
API_ID = 22121081
API_HASH = "40aa45abc830f38901ac455674812256"
SESSION_NAME = "user_session"  # your Pyrogram session file

# === Cloudflare Worker URL ===
WORKER_URL = "https://moviestream.dawerraza068.workers.dev"

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
client = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

HLS_FOLDER = "hls_videos"
os.makedirs(HLS_FOLDER, exist_ok=True)

# --- Telegram media handler ---
@client.on_message(filters.video | filters.document)
async def handle_media(c, message):
    media = message.video or message.document
    file_name = media.file_name or "video.mp4"
    local_path = os.path.join(HLS_FOLDER, file_name)

    # Download file
    await c.download_media(media, file_name=local_path)

    # Decide if HLS needed
    if os.path.getsize(local_path) > 50*1024*1024:  # >50MB
        hls_folder = os.path.join(HLS_FOLDER, file_name.split('.')[0])
        os.makedirs(hls_folder, exist_ok=True)
        playlist = os.path.join(hls_folder, "index.m3u8")

        subprocess.run([
            "ffmpeg", "-i", local_path,
            "-codec: copy", "-start_number", "0",
            "-hls_time", "10", "-hls_list_size", "0",
            "-f", "hls", playlist
        ], check=True)

        stream_url = f"{WORKER_URL}/hls/{file_name.split('.')[0]}/index.m3u8"
    else:
        # Small file → direct Telegram
        stream_url = f"{WORKER_URL}/file?file_id={media.file_id}"

    await message.reply_text(
        f"🎬 **Stream Ready!**\n"
        f"📁 `{file_name}`\n"
        f"🌐 Watch here:\n👉 {stream_url}"
    )

# --- Flask test endpoint ---
@app.route("/")
def home():
    return "✅ Telegram HLS Stream Server Running!"

# --- Run Flask ---
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

# --- Start bot + Flask ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    client.run()
