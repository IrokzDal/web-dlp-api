"""
Automatic cleanup routine for old files and jobs.
"""
import os
import time
import threading
from pathlib import Path
from app.queue import get_all_jobs, delete_job
from app.utils import log_info, log_warning

CLEANUP_INTERVAL = 300  # 5 minutes
MAX_FILE_AGE = 600  # 10 minutes
DOWNLOADS_DIR = Path(__file__).parent / "downloads"


def cleanup_old_files():
    """
    Remove files and jobs older than MAX_FILE_AGE.
    This function runs periodically in a background thread.
    """
    while True:
        try:
            log_info("Starting cleanup routine...")
            current_time = time.time()
            
            # Get all jobs
            all_jobs = get_all_jobs()
            
            for job_id, job_data in list(all_jobs.items()):
                created_at = job_data.get('created_at', current_time)
                age = current_time - created_at
                
                # If job is older than MAX_FILE_AGE
                if age > MAX_FILE_AGE:
                    # Delete associated file if it exists
                    filename = job_data.get('filename')
                    if filename:
                        file_path = DOWNLOADS_DIR / filename
                        if file_path.exists():
                            try:
                                file_path.unlink()
                                log_info(f"Deleted old file: {filename}")
                            except Exception as e:
                                log_warning(f"Failed to delete file {filename}: {e}")
                    
                    # Delete job metadata
                    delete_job(job_id)
                    log_info(f"Removed old job: {job_id}")
            
            # Also check for orphaned files in downloads directory
            if DOWNLOADS_DIR.exists():
                for file_path in DOWNLOADS_DIR.iterdir():
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > MAX_FILE_AGE:
                            try:
                                file_path.unlink()
                                log_info(f"Deleted orphaned file: {file_path.name}")
                            except Exception as e:
                                log_warning(f"Failed to delete orphaned file {file_path.name}: {e}")
            
            log_info(f"Cleanup complete. Next cleanup in {CLEANUP_INTERVAL} seconds.")
            
        except Exception as e:
            log_warning(f"Error during cleanup: {e}")
        
        # Wait for next cleanup cycle
        time.sleep(CLEANUP_INTERVAL)


def start_cleanup_thread():
    """
    Start the cleanup routine in a background thread.
    """
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()
    log_info("Cleanup thread started")
