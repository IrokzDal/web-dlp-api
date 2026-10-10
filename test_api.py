"""
Test script to verify the web-dlp API functionality.
This script helps test the API without needing Docker.
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def print_status(message, status="INFO"):
    """Print formatted status message."""
    symbols = {"INFO": "ℹ", "SUCCESS": "✓", "ERROR": "✗", "WAIT": "⏳"}
    print(f"{symbols.get(status, 'ℹ')} {message}")


def test_health_check():
    """Test the health check endpoint."""
    print_status("Testing health check endpoint...", "INFO")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "YT-API running":
                print_status("Health check passed!", "SUCCESS")
                return True
        print_status(f"Health check failed: {response.text}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Connection error: {e}", "ERROR")
        return False


def test_create_job(url, format="mp3"):
    """Test creating a download job."""
    print_status(f"Creating download job for {format.upper()}...", "INFO")
    try:
        response = requests.post(
            f"{BASE_URL}/request",
            json={"url": url, "format": format}
        )
        if response.status_code == 200:
            data = response.json()
            job_id = data.get("job_id")
            print_status(f"Job created: {job_id}", "SUCCESS")
            return job_id
        else:
            print_status(f"Failed to create job: {response.text}", "ERROR")
            return None
    except Exception as e:
        print_status(f"Error creating job: {e}", "ERROR")
        return None


def test_job_status(job_id):
    """Test checking job status."""
    print_status("Checking job status...", "WAIT")
    try:
        response = requests.get(f"{BASE_URL}/status?id={job_id}")
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            progress = data.get("progress", 0)
            print_status(f"Status: {status} ({progress}%)", "INFO")
            return data
        else:
            print_status(f"Failed to get status: {response.text}", "ERROR")
            return None
    except Exception as e:
        print_status(f"Error getting status: {e}", "ERROR")
        return None


def wait_for_completion(job_id, max_wait=120):
    """Wait for job to complete."""
    print_status("Waiting for job to complete...", "WAIT")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_data = test_job_status(job_id)
        if not status_data:
            return False
        
        status = status_data.get("status")
        
        if status == "finished":
            print_status("Job completed!", "SUCCESS")
            return True
        elif status == "error":
            error = status_data.get("error", "Unknown error")
            print_status(f"Job failed: {error}", "ERROR")
            return False
        
        time.sleep(3)
    
    print_status("Timeout waiting for job", "ERROR")
    return False


def test_download_result(job_id, output_filename):
    """Test downloading the result file."""
    print_status("Downloading result...", "INFO")
    try:
        response = requests.get(f"{BASE_URL}/result?id={job_id}")
        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(response.content)
            print_status(f"File downloaded: {output_filename}", "SUCCESS")
            return True
        else:
            print_status(f"Download failed: {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Error downloading: {e}", "ERROR")
        return False


def test_rate_limiting():
    """Test rate limiting (5 requests per minute)."""
    print_status("Testing rate limiting...", "INFO")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    for i in range(6):
        response = requests.post(
            f"{BASE_URL}/request",
            json={"url": test_url, "format": "mp3"}
        )
        if i < 5:
            if response.status_code == 200:
                print_status(f"Request {i+1}/6 accepted", "SUCCESS")
            else:
                print_status(f"Request {i+1}/6 failed unexpectedly", "ERROR")
                return False
        else:
            if response.status_code == 429:
                print_status("Rate limit correctly enforced!", "SUCCESS")
                return True
            else:
                print_status("Rate limit not working!", "ERROR")
                return False
    
    return True


def test_invalid_url():
    """Test URL validation."""
    print_status("Testing URL validation...", "INFO")
    invalid_urls = [
        "https://example.com/video",
        "https://vimeo.com/123456",
        "not-a-url"
    ]
    
    for url in invalid_urls:
        response = requests.post(
            f"{BASE_URL}/request",
            json={"url": url, "format": "mp3"}
        )
        if response.status_code == 400:
            print_status(f"Invalid URL correctly rejected: {url}", "SUCCESS")
        else:
            print_status(f"Invalid URL not rejected: {url}", "ERROR")
            return False
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("web-dlp API Test Suite")
    print("="*50 + "\n")
    
    # Test 1: Health check
    if not test_health_check():
        print_status("API is not running. Start it with:", "ERROR")
        print("  python app/worker.py & uvicorn app.main:app --reload")
        sys.exit(1)
    
    print("\n" + "-"*50 + "\n")
    
    # Test 2: Invalid URL validation
    test_invalid_url()
    
    print("\n" + "-"*50 + "\n")
    
    # Test 3: Create and complete a download job
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Short video
    job_id = test_create_job(test_url, "mp3")
    
    if job_id:
        if wait_for_completion(job_id):
            test_download_result(job_id, "test_download.mp3")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 4: Rate limiting
    print_status("Waiting 60s before rate limit test...", "WAIT")
    time.sleep(60)
    test_rate_limiting()
    
    print("\n" + "="*50)
    print_status("Test suite completed!", "SUCCESS")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
