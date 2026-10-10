# Use Python 3.11 slim image
FROM python:3.11-slim

# Install FFmpeg (required by yt-dlp)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --upgrade --no-cache-dir yt-dlp

# Copy application code
COPY app/ ./app/

# Create downloads directory
RUN mkdir -p /app/downloads

# Expose port 8000
EXPOSE 8000

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

# Start only the API server (serverless compliant)
# Use shell expansion for PORT variable
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
