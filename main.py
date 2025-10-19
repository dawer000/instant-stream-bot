from flask import Flask, request, jsonify, send_from_directory
import os, subprocess, requests, uuid

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL", "https://instant-stream-bot-production.up.railway.app")  # Replace later

@app.route('/')
def home():
    return "✅ Telegram HLS Converter is running!"

# ✅ Serve .m3u8 and .ts files publicly
@app.route('/hls/<path:filename>')
def serve_hls(filename):
    return send_from_directory('hls', filename)

@app.route('/tg', methods=['POST'])
def tg_webhook():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "Invalid request"}), 400

    message = data["message"]
    chat_id = message["chat"]["id"]

    if "video" not in message and "document" not in message:
        send_message(chat_id, "❌ Please send a video file.")
        return "ok"

    media = message.get("video") or message.get("document")
    file_id = media["file_id"]
    file_name = media.get("file_name", f"{uuid.uuid4()}.mp4")

    # Get Telegram file path
    file_path = get_file_path(file_id)
    if not file_path:
        send_message(chat_id, "❌ Could not fetch file.")
        return "ok"

    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    local_path = f"{file_name}"
    send_message(chat_id, f"⬇️ Downloading `{file_name}` ...")

    with requests.get(file_url, stream=True) as r:
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Convert to HLS
    output_dir = f"hls/{file_id}"
    os.makedirs(output_dir, exist_ok=True)
    hls_playlist = f"{output_dir}/index.m3u8"

    send_message(chat_id, "⏳ Converting to HLS...")

    try:
              subprocess.run([
            "ffmpeg", "-i", local_path,
            "-preset", "veryfast",
            "-g", "48", "-sc_threshold", "0",
            "-map", "0:v:0", "-map", "0:a:0",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "128k",
            "-hls_time", "4", "-hls_playlist_type", "vod",
            "-hls_segment_filename", f"{output_dir}/segment_%03d.ts",
            hls_playlist
        ], check=True)


        # ✅ Correct HLS public link
        public_url = f"{APP_URL}/hls/{file_id}/index.m3u8"
        send_message(chat_id, f"✅ Video ready!\n🎬 {public_url}")

    except Exception as e:
        send_message(chat_id, f"❌ Conversion failed: {str(e)}")

    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

    return "ok"

def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
    res = requests.get(url).json()
    return res["result"]["file_path"] if "result" in res else None

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

if __name__ == '__main__':
    os.makedirs("hls", exist_ok=True)
    app.run(host="0.0.0.0", port=8080)
