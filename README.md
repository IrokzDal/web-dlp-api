# web-dlp API

A queue-based YouTube downloader API using yt-dlp. Download YouTube videos as MP4 or extract audio as MP3 through a simple REST API.

[![Featured on Orynth](https://orynth.dev/api/badge/web-dlp-api?theme=dark&style=default)](https://orynth.dev/projects/web-dlp-api)

## Features

- ✅ **Format Selection**: Download as MP4 (video) or MP3 (audio)
- ✅ **Queue System**: Background job processing for stable performance
- ✅ **Auto Cleanup**: Files automatically deleted after 10 minutes
- ✅ **Rate Limiting**: 5 requests per IP per minute
- ✅ **YouTube Only**: URL validation for security
- ✅ **Keep-Alive Support**: Health check endpoint for uptime monitoring
- ✅ **Docker Ready**: Optimized for Railway deployment

## API Endpoints

### 1. Health Check
```bash
GET /
```

**Response:**
```json
{
  "status": "YT-API running"
}
```

---

### 2. Create Download Job
```bash
POST /request
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format": "mp3"
}
```

**Parameters:**
- `url` (required): YouTube video URL
- `format` (optional): `"mp3"` for audio or `"mp4"` for video (default: "mp4")

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued"
}
```

---

### 3. Check Job Status
```bash
GET /status?id=<job_id>
```

**Response:**
```json
{
  "status": "processing",
  "progress": 60,
  "error": null
}
```

**Possible status values:**
- `queued` - Job is waiting to be processed
- `processing` - Download in progress
- `finished` - Download complete, ready to retrieve
- `error` - Download failed

---

### 4. Download Result
```bash
GET /result?id=<job_id>
```

**Response:**
- If ready: Returns the file as a download
- If not ready:
```json
{
  "error": "not_ready",
  "status": "processing"
}
```

---

## Usage Examples

### Using cURL

```bash
# 1. Create a job
curl -X POST http://localhost:8000/request \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","format":"mp3"}'

# 2. Check status
curl "http://localhost:8000/status?id=YOUR_JOB_ID"

# 3. Download file when ready
curl "http://localhost:8000/result?id=YOUR_JOB_ID" --output download.mp3
```

### Using JavaScript (Fetch API)

```javascript
// 1. Create a job
const response = await fetch('http://localhost:8000/request', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    format: 'mp3'
  })
});
const { job_id } = await response.json();

// 2. Poll for status
const checkStatus = async () => {
  const statusRes = await fetch(`http://localhost:8000/status?id=${job_id}`);
  const { status } = await statusRes.json();
  return status;
};

// 3. Download when ready
while (await checkStatus() !== 'finished') {
  await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s
}

window.location.href = `http://localhost:8000/result?id=${job_id}`;
```

---

## Local Development

### Using Docker

```bash
# Build the image
docker build -t web-dlp .

# Run the container
docker run -p 8000:8000 web-dlp
```

The API will be available at `http://localhost:8000`

### Using Python (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Install yt-dlp and FFmpeg
# Windows: Download FFmpeg from ffmpeg.org
# Mac: brew install ffmpeg
# Linux: apt-get install ffmpeg

# Start worker (in one terminal)
python app/worker.py

# Start API (in another terminal)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Railway Deployment

1. **Connect to Railway**:
   - Push your code to GitHub
   - Create a new Railway project
   - Connect your GitHub repository

2. **Deploy**:
   - Railway will automatically detect the Dockerfile
   - The app will build and deploy

3. **Environment**:
   - No environment variables needed
   - Port 8000 is automatically exposed

4. **Keep-Alive** (for free tier):
   - Use [cron-job.org](https://cron-job.org) to ping `https://your-app.railway.app/` every 5 minutes
   - This prevents the free-tier app from sleeping

---

## Rate Limits & Restrictions

- **Rate Limit**: 5 requests per IP per minute
- **URL Validation**: Only YouTube URLs accepted
- **File Lifetime**: Files auto-delete after 10 minutes
- **Video Quality**: MP4 limited to 720p max (to save bandwidth)
- **Timeout**: Downloads timeout after 5 minutes

---

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Downloader**: yt-dlp
- **Queue**: Python multiprocessing
- **Server**: Uvicorn
- **Container**: Docker

---

## Project Structure

```
web-dlp API/
├── app/
│   ├── main.py       # FastAPI application
│   ├── worker.py     # Background download worker
│   ├── queue.py      # Job queue management
│   ├── cleanup.py    # Automatic file cleanup
│   ├── utils.py      # Validation & rate limiting
│   └── downloads/    # Temporary file storage
├── Dockerfile        # Docker configuration
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## License

This project is provided as-is for educational purposes.

---

## Support

For issues or questions, please open an issue on GitHub.
