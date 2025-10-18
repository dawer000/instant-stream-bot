import os
import threading
from flask import Flask, request, send_file
from pyrogram import Client, filters

# === Telegram Config ===
API_ID = 22121081
API_HASH = "40aa45abc830f38901ac455674812256"
BOT_TOKEN = "8425638442:AAFdXiLbKuN57hM4krrbIf0AT8OqJY0Pe3o"

# === Cloudflare Worker URL ===
WORKER_URL = "https://moviestream.dawerraza068.workers.dev"

# === Local folders ===
HLS_FOLDER = "hls_videos"
os.makedirs(HLS_FOLDER, exist_ok=True)

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# --- Telegram handler ---
@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"
    local_path = os.path.join(HLS_FOLDER, file_name)

    try:
        # Download media
        await client.download_media(media, file_name=local_path)
        print(f"✅ Downloaded {file_name}")

        # Check size for HLS conversion (e.g., >50MB)
        if os.path.getsize(local_path) > 50 * 1024 * 1024:
            # Convert to HLS
            hls_folder_path = os.path.join(HLS_FOLDER, file_name.split('.')[0])
            os.makedirs(hls_folder_path, exist_ok=True)
            hls_playlist = os.path.join(hls_folder_path, "index.m3u8")

            # FFmpeg HLS conversion
            import subprocess
            subprocess.run([
                "ffmpeg", "-i", local_path,
                "-codec:", "copy",
                "-start_number", "0",
                "-hls_time", "10",
                "-hls_list_size", "0",
                "-f", "hls", hls_playlist
            ], check=True)

            stream_url = f"{WORKER_URL}/hls/{file_name.split('.')[0]}/index.m3u8"
        else:
            # Small file → direct download link via Worker
            stream_url = f"{WORKER_URL}/file?file_id={file_id}"

        # Reply to user
        await message.reply_text(
            f"🎬 **Your Stream is Ready!**\n\n"
            f"📁 `{file_name}`\n"
            f"🌐 Stream instantly here:\n👉 {stream_url}",
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply_text(f"❌ Failed to process: {e}")
        print("❌ Error:", e)


# --- Flask endpoints ---
@app.route("/")
def home():
    return "✅ Instant Telegram Stream Bot Running!"

# Serve small files
@app.route("/file")
def serve_file():
    file_id = request.args.get("file_id")
    if not file_id:
        return "❌ No file_id provided", 400

    try:
        local_file = os.path.join(HLS_FOLDER, f"{file_id}.mp4")
        if not os.path.exists(local_file):
            # Download file temporarily
            bot.download_media(file_id, file_name=local_file)
        return send_file(local_file, mimetype="video/mp4")
    except Exception as e:
        return f"❌ Error: {e}", 500


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    # Start Flask
    threading.Thread(target=run_flask).start()
    # Start Pyrogram bot
    bot.run()
