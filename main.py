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
    send_message(chat_id, "⏳ Converting to HLS...")

    os.makedirs("hls", exist_ok=True)
    output_dir = f"hls/{file_id}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        subprocess.run([
            "ffmpeg", "-i", file_url,
            "-hls_time", "10", "-hls_list_size", "0",
            "-f", "hls", f"{output_dir}/index.m3u8"
        ], check=True)
    except Exception as e:
        send_message(chat_id, f"❌ Conversion failed: {str(e)}")
        return "ok"

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
