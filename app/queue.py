"""
Queue system for managing download jobs using threading (Windows-compatible).
"""
import queue
import threading
from typing import Dict, Any
import uuid
import time

# Thread-safe dictionary
# job_queue removed for serverless compatibility
job_statuses: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def create_job(url: str, format: str) -> str:
    """
    Create a new download job.
    
    Args:
        url: YouTube video URL
        format: Output format (mp3 or mp4)
    
    Returns:
        job_id: Unique identifier for the job
    """
    job_id = str(uuid.uuid4())
    
    job_data = {
        'job_id': job_id,
        'url': url,
        'format': format,
        'status': 'queued',
        'progress': 0,
        'error': None,
        'filename': None,
        'created_at': time.time()
    }
    
    # Store job status (thread-safe)
    with _lock:
        job_statuses[job_id] = job_data
    
    # Queue usage removed for serverless compatibility
    # The job will be processed via FastAPI BackgroundTasks
    
    return job_id


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the current status of a job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        Job status dictionary or None if not found
    """
    with _lock:
        return job_statuses.get(job_id, {}).copy()


def update_job_status(job_id: str, **kwargs):
    """
    Update job status with new information.
    
    Args:
        job_id: Job identifier
        **kwargs: Fields to update (status, progress, error, filename)
    """
    with _lock:
        if job_id in job_statuses:
            job_statuses[job_id].update(kwargs)


def delete_job(job_id: str):
    """
    Delete a job from the status tracking.
    
    Args:
        job_id: Job identifier
    """
    with _lock:
        if job_id in job_statuses:
            del job_statuses[job_id]


def get_all_jobs() -> Dict[str, Dict[str, Any]]:
    """
    Get all jobs (used for cleanup).
    
    Returns:
        Dictionary of all jobs
    """
    with _lock:
        return job_statuses.copy()
