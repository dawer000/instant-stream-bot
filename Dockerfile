# Use lightweight Python image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8080

# Run the bot
CMD ["python", "app.py"]
