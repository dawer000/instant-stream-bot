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

        # ffmpeg
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
            f"🌐 Watch here:\n👉 {stream_url}"
        )

    except Exception as e:
        print("[ERROR]", e)
        await message.reply_text(f"❌ Failed: {e}")
