#!/bin/bash
set -e

# Install FFmpeg
apt-get update -y
apt-get install -y ffmpeg

# Print version to confirm installation
ffmpeg -version
