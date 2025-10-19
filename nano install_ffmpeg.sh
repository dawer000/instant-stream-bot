#!/bin/bash
# Update package list and install ffmpeg

echo "📦 Updating system packages..."
sudo apt update -y

echo "🎬 Installing FFmpeg..."
sudo apt install ffmpeg -y

echo "✅ FFmpeg installation completed!"
ffmpeg -version
