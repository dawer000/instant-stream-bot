import os
import threading
from flask import Flask, request, Response
from pyrogram import Client, filters

# === Telegram Config ===
API_ID = 22121081
API_HASH = "40aa45abc830f38901ac455674812256"
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# === Cloudflare Worker URL ===
WORKER_URL = "https://moviestream.dawerraza068.workers.dev"

# === Initialize Flask + Pyrogram ===
app = Flask(__name__)
bot = Client("instant_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Handle media messages ---
@bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    media = message.video or message.document
    file_id = media.file_id
    file_name = media.file_name or "video.mp4"

    # Cloudflare Worker instant play link
    stream_url = f"{WORKER_URL}/stream?file_id={file_id}"

    await message.reply_text(
        f"🎬 **Your Stream is Ready!**\n\n"
        f"📁 `{file_name}`\n"
        f"🌐 Watch instantly:\n👉 {stream_url}",
        disable_web_page_preview=True
    )

# --- Stream endpoint (Railway handles range streaming) ---
@app.route("/stream")
def stream():
    file_id = request.args.get("file_id")
    if not file_id:
        return "❌ No file_id provided", 400

    range_header = request.headers.get("Range", None)
    byte1, byte2 = 0, None

    if range_header:
        import re
        m = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if m:
            g1, g2 = m.groups()
            byte1 = int(g1)
            if g2:
                byte2 = int(g2)

    async def gen():
        try:
            # Telegram get_file() returns a generator for chunks
            async for chunk in bot.get_file(file_id, offset=byte1):
                yield chunk
        except Exception as e:
            print("❌ Stream Error:", e)

    resp = Response(gen(), status=206 if range_header else 200, mimetype="video/mp4")
    if range_header:
        resp.headers.add("Content-Range", f"bytes {byte1}-{'' if byte2 is None else byte2}/*")
        resp.headers.add("Accept-Ranges", "bytes")
    return resp

# --- Flask home ---
@app.route("/")
def home():
    return "✅ Instant Telegram Stream Bot Running!"

# --- Run Flask ---
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run()
