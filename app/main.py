"""
FastAPI main application with all API endpoints.
"""
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
from app.queue import create_job, get_job_status
from app.worker import download_video
from app.utils import is_valid_youtube_url, check_rate_limit, log_info, log_error
from app.cleanup import start_cleanup_thread

# Initialize FastAPI app with professional metadata
app = FastAPI(
    title="web-dlp API",
    description="""
    **YouTube Downloader API** powered by yt-dlp
    
    A queue-based REST API for downloading YouTube videos and extracting audio.
    
    ## Features
    - **MP3** - Extract audio only (192K quality)
    - **MP4** - Download video (max 720p)
    - **Queue System** - Non-blocking background processing
    - **Rate Limited** - 5 requests per IP per minute
    - **Auto Cleanup** - Files deleted after 10 minutes
    
    ## Quick Start
    1. Create a job with `POST /request`
    2. Check status with `GET /status?id={job_id}`
    3. Download file with `GET /result?id={job_id}`
    
    For detailed documentation, visit the [custom docs page](https://web-dlp-api-production.up.railway.app/docs).
    """,
    version="1.0.0",
    contact={
        "name": "web-dlp API",
        "url": "https://github.com/Solez-ai/web-dlp-api",
    },
    license_info={
        "name": "MIT",
    },
    # Disable default docs to use custom
    docs_url=None,
    redoc_url=None,
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve custom documentation
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    """Serve the custom professional documentation page."""
    docs_path = static_dir / "docs.html"
    if docs_path.exists():
        with open(docs_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        return HTMLResponse(content="<h1>Documentation not found</h1><p>Please ensure docs.html exists in the static directory.</p>", status_code=404)

# OpenAPI JSON endpoint (for programmatic access)
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    """Return OpenAPI spec as JSON."""
    return app.openapi()


# Start cleanup thread on startup
@app.on_event("startup")
async def startup_event():
    """Initialize background threads on application startup."""
    # Start cleanup thread
    start_cleanup_thread()
    
    # Worker thread removed for serverless compatibility.
    # Jobs are now handled via BackgroundTasks.
    
    log_info("web-dlp API started successfully")
    
    log_info("web-dlp API started successfully")


# Pydantic models
class JobRequest(BaseModel):
    """Request model for creating a download job."""
    url: str = Field(..., description="YouTube video URL")
    format: str = Field("mp4", description="Output format: 'mp3' (audio) or 'mp4' (video)")


class JobCreateResponse(BaseModel):
    """Response model for job creation."""
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    status: str
    progress: int
    error: str | None = None


# API Endpoints

@app.get("/")
async def health_check():
    """
    Health check endpoint for keep-alive pings.
    
    Returns:
        Status message indicating the API is running
    """
    return {"status": "YT-API running"}


@app.post("/request", response_model=JobCreateResponse)
async def create_download_job(job_request: JobRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Create a new download job.
    
    - **url**: YouTube video link
    - **format**: Output format - "mp3" (audio only) or "mp4" (video)
    
    Returns:
        Job ID and initial status
    """
    # Get client IP
    client_ip = request.client.host
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        log_error(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 5 requests per minute."
        )
    
    # Validate URL
    if not is_valid_youtube_url(job_request.url):
        log_error(f"Invalid YouTube URL: {job_request.url}")
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Only YouTube URLs are supported."
        )
    
    # Validate format
    if job_request.format not in ['mp3', 'mp4']:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Use 'mp3' or 'mp4'."
        )
    
    # Create job
    try:
        job_id = create_job(job_request.url, job_request.format)
        
        # Add background task
        background_tasks.add_task(download_video, job_id, job_request.url, job_request.format)
        
        log_info(f"Created job {job_id} for {job_request.url} ({job_request.format})")
        
        return JobCreateResponse(job_id=job_id, status="queued")
    
    except Exception as e:
        log_error(f"Failed to create job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create download job"
        )


@app.get("/status", response_model=JobStatusResponse)
async def get_status(id: str):
    """
    Get the status of a download job.
    
    - **id**: Job ID returned from /request
    
    Returns:
        Current job status and progress (0-100)
    """
    job_data = get_job_status(id)
    
    if not job_data:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    return JobStatusResponse(
        status=job_data.get('status', 'unknown'),
        progress=job_data.get('progress', 0),
        error=job_data.get('error')
    )


@app.get("/result")
async def get_result(id: str):
    """
    Download the completed file.
    
    - **id**: Job ID returned from /request
    
    Returns:
        File download if ready, or error message if not ready
    """
    job_data = get_job_status(id)
    
    if not job_data:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    # Check if job is finished
    if job_data.get('status') != 'finished':
        status = job_data.get('status', 'unknown')
        return JSONResponse(
            status_code=400,
            content={"error": "not_ready", "status": status}
        )
    
    # Get file path
    filename = job_data.get('filename')
    if not filename:
        raise HTTPException(
            status_code=500,
            detail="File not available"
        )
    
    downloads_dir = Path(__file__).parent / "downloads"
    file_path = downloads_dir / filename
    
    if not file_path.exists():
        log_error(f"File not found for job {id}: {filename}")
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    # Determine media type
    media_type = "audio/mpeg" if filename.endswith('.mp3') else "video/mp4"
    
    log_info(f"Serving file for job {id}: {filename}")
    
    # Return file
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc.detail)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    log_error(f"Internal error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
