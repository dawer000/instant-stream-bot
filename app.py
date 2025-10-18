import os
import threading
import subprocess
from flask import Flask
from pyrogram import Client, filters
import ffmpeg_static  # Portable ffmpeg binary

# === Telegram Config ===
API_ID = 22121081
API_HASH = "40aa45abc830f38901ac455674812256"
BOT_TOKEN = "8425638442:AAFdXiLbKuN57hM4krrbIf0AT8OqJY0Pe3o"

# === Cloudflare Worker URL (for instant streaming) ===
WORKER_URL = "https://moviestream.dawerraza068.workers.dev"

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Folder for downloaded and HLS files
HLS_FOLDER = "hls_videos"
os.makedirs(HLS_FOLDER, exist_ok=True)

# --- Handle media messages ---
@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"

    local_path = os.path.join(HLS_FOLDER, file_name)
    await client.download_media(file_id, file_name=local_path)

    # Convert to HLS using ffmpeg-static
    hls_folder_path = os.path.join(HLS_FOLDER, file_name.split('.')[0])
    os.makedirs(hls_folder_path, exist_ok=True)
    hls_playlist = os.path.join(hls_folder_path, "index.m3u8")

    subprocess.run([
        ffmpeg_static.binary, "-i", local_path,
        "-codec: copy", "-start_number", "0",
        "-hls_time", "10", "-hls_list_size", "0",
        "-f", "hls", hls_playlist
    ], check=True)

    stream_url = f"{WORKER_URL}/hls/{file_name.split('.')[0]}/index.m3u8"

    await message.reply_text(
        f"🎬 **Your HLS Stream is Ready!**\n\n"
        f"📁 `{file_name}`\n"
        f"🌐 Watch instantly:\n👉 {stream_url}"
    )

# --- Flask endpoint for testing ---
@app.route("/")
def home():
    return "✅ Instant HLS Telegram Bot Running!"

# --- Run Flask ---
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

# --- Main ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run()
