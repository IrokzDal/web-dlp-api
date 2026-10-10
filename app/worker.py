"""
Background worker process for downloading videos using yt-dlp.
"""
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from app.queue import update_job_status
from app.utils import log_info, log_error

DOWNLOADS_DIR = Path(__file__).parent / "downloads"


def download_video(job_id: str, url: str, format: str):
    """
    Download video or audio using yt-dlp.
    
    Args:
        job_id: Unique job identifier
        url: YouTube video URL
        format: Output format (mp3 or mp4)
    """
    try:
        log_info(f"Starting download for job {job_id}: {url} ({format})")
        update_job_status(job_id, status='processing', progress=10)
        
        # Ensure downloads directory exists
        DOWNLOADS_DIR.mkdir(exist_ok=True)
        
        # Determine output filename
        if format == 'mp3':
            output_filename = f"{job_id}.mp3"
            output_path = DOWNLOADS_DIR / output_filename
            
            # yt-dlp command for audio extraction
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192K',
                '--output', str(output_path),
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                url
            ]
        else:  # mp4
            output_filename = f"{job_id}.mp4"
            output_path = DOWNLOADS_DIR / output_filename
            
            # yt-dlp command for video download (720p or best)
            cmd = [
                'yt-dlp',
                '--format', 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                '--merge-output-format', 'mp4',
                '--output', str(output_path),
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                url
            ]
        
        update_job_status(job_id, status='processing', progress=30)
        
        # Execute yt-dlp
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            error_msg = result.stderr or "Download failed"
            log_error(f"Job {job_id} failed: {error_msg}")
            update_job_status(
                job_id,
                status='error',
                error=error_msg,
                progress=0
            )
            return
        
        update_job_status(job_id, status='processing', progress=90)
        
        # Verify file exists
        if not output_path.exists():
            log_error(f"Job {job_id}: File not found after download")
            update_job_status(
                job_id,
                status='error',
                error='File not created',
                progress=0
            )
            return
        
        # Mark as finished
        update_job_status(
            job_id,
            status='finished',
            progress=100,
            filename=output_filename
        )
        log_info(f"Job {job_id} completed successfully: {output_filename}")
        
    except subprocess.TimeoutExpired:
        log_error(f"Job {job_id} timed out")
        update_job_status(
            job_id,
            status='error',
            error='Download timeout (5 minutes)',
            progress=0
        )
    except Exception as e:
        log_error(f"Job {job_id} error: {str(e)}")
        update_job_status(
            job_id,
            status='error',
            error=str(e),
            progress=0
        )


# worker_process and __main__ block removed for serverless compatibility.
# The download_video function is called directly by FastAPI BackgroundTasks.
