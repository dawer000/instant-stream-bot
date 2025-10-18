from flask import Flask, request, jsonify
import os, subprocess, requests

app = Flask(__name__)

# Simple endpoint to test
@app.route('/')
def home():
    return "✅ Telegram HLS Converter is running!"

# Telegram webhook endpoint
@app.route('/tg', methods=['POST'])
def tg_webhook():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "invalid request"}), 400

    chat_id = data["message"]["chat"]["id"]

    if "video" not in data["message"]:
        send_message(chat_id, "❌ Please send a video file.")
        return "ok"

    # Telegram video file_id
    file_id = data["message"]["video"]["file_id"]
    file_path = get_file_path(file_id)
    if not file_path:
        send_message(chat_id, "❌ Could not fetch file.")
        return "ok"

    file_url = f"https://api.telegram.org/file/bot{os.getenv('BOT_TOKEN')}/{file_path}"

    send_message(chat_id, "⏳ Downloading video...")

    # Create directories
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("hls", exist_ok=True)

    # Local paths
    local_path = f"downloads/{file_id}.mp4"
    output_dir = f"hls/{file_id}"
    os.makedirs(output_dir, exist_ok=True)
    hls_playlist = f"{output_dir}/index.m3u8"

    # Download the video
    try:
        r = requests.get(file_url, stream=True)
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        send_message(chat_id, f"❌ Download failed: {str(e)}")
        return "ok"

    send_message(chat_id, "⏳ Converting to HLS...")

    # Convert to HLS
    try:
        subprocess.run([
            "ffmpeg", "-i", local_path,
            "-c:v", "copy", "-c:a", "aac",
            "-strict", "-2",
            "-hls_time", "5",
            "-hls_list_size", "0",
            "-hls_flags", "delete_segments",
            "-f", "hls", hls_playlist
        ], check=True)
    except Exception as e:
        send_message(chat_id, f"❌ Conversion failed: {str(e)}")
        return "ok"

    # Public URL (Cloudflare Worker / Railway domain)
    public_url = f"{os.getenv('APP_URL')}/{output_dir}/index.m3u8"
    send_message(chat_id, f"✅ HLS ready!\n🎬 {public_url}")
    return "ok"

def get_file_path(file_id):
    url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/getFile?file_id={file_id}"
    res = requests.get(url).json()
    return res["result"]["file_path"] if "result" in res else None

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
