from flask import Flask, request, jsonify
import os, subprocess, requests, uuid

app = Flask(__name__)

BOT_TOKEN = "8425638442:AAFdXiLbKuN57hM4krrbIf0AT8OqJY0Pe3o"
APP_URL = "https://moviestream.dawerraza068.workers.dev"  # Cloudflare Worker

@app.route('/')
def home():
    return "✅ Telegram HLS Converter is running!"

@app.route('/tg', methods=['POST'])
def tg_webhook():
    data = request.json
    if not data or "message" not in data:
        return jsonify({"error": "Invalid request"}), 400

    message = data["message"]
    chat_id = message["chat"]["id"]

    # Check for video/document
    if "video" not in message and "document" not in message:
        send_message(chat_id, "❌ Please send a video file.")
        return "ok"

    media = message.get("video") or message.get("document")
    file_id = media["file_id"]
    file_name = media.get("file_name", f"{uuid.uuid4()}.mp4")

    # Get file path from Telegram
    file_path = get_file_path(file_id)
    if not file_path:
        send_message(chat_id, "❌ Could not fetch file from Telegram.")
        return "ok"

    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    local_path = f"{file_name}"
    send_message(chat_id, f"⬇️ Downloading `{file_name}` ...")

    # Download the file
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
            "-c:v", "copy", "-c:a", "aac",
            "-strict", "-2",
            "-hls_time", "5",
            "-hls_list_size", "0",
            "-f", "hls", hls_playlist
        ], check=True)

        public_url = f"{APP_URL}/hls/{file_id}/index.m3u8"
        send_message(chat_id, f"✅ HLS ready!\n🎬 {public_url}")

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
