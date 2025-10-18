import os
import threading
from flask import Flask
from pyrogram import Client, filters
import subprocess

# === Telegram Config ===
API_ID = 22121081
API_HASH = "40aa45abc830f38901ac455674812256"
BOT_TOKEN = "8425638442:AAFdXiLbKuN57hM4krrbIf0AT8OqJY0Pe3o"

# === Cloudflare Worker URL ===
WORKER_URL = "https://moviestream.dawerraza068.workers.dev"

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# HLS folder
HLS_FOLDER = "hls_videos"
os.makedirs(HLS_FOLDER, exist_ok=True)

# --- Telegram media handler ---
@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    try:
        media = message.video or message.document
        file_name = media.file_name or "video.mp4"

        await message.reply_text(f"⬇️ Downloading `{file_name}` ...")

        local_path = os.path.join(HLS_FOLDER, file_name)
        await client.download_media(media, file_name=local_path)
        print(f"[DEBUG] Downloaded: {local_path}")
        await message.reply_text(f"✅ Downloaded `{file_name}`")

        # Convert to HLS
        hls_folder = os.path.join(HLS_FOLDER, file_name.split('.')[0])
        os.makedirs(hls_folder, exist_ok=True)
        hls_playlist = os.path.join(hls_folder, "index.m3u8")

        # ffmpeg command
        result = subprocess.run([
            "ffmpeg", "-i", local_path,
            "-c", "copy",
            "-start_number", "0",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-f", "hls",
            hls_playlist
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print("[ERROR] FFmpeg failed:", result.stderr)
            await message.reply_text("❌ FFmpeg failed: see logs")
            return

        # Cloudflare Worker link
        stream_url = f"{WORKER_URL}/hls/{file_name.split('.')[0]}/index.m3u8"
        await message.reply_text(
            f"🎬 **Your HLS Stream is Ready!**\n\n"
            f"📁 `{file_name}`\n"
            f"🌐 Watch instantly here:\n👉 {stream_url}"
        )

    except Exception as e:
        print("[ERROR]", e)
        await message.reply_text(f"❌ Failed: {e}")

# --- Flask test endpoint ---
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
