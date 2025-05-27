#!/usr/bin/env python
"""
Script to run the development server and Celery workers.
"""
import os
import sys
import subprocess
import time
import signal
import atexit

# Global variables to store process objects
server_process = None
celery_worker_process = None
celery_beat_process = None

def cleanup():
    """Clean up function to terminate all processes on exit."""
    print("\nShutting down processes...")
    
    if server_process:
        print("Terminating Django server...")
        server_process.terminate()
    
    if celery_worker_process:
        print("Terminating Celery worker...")
        celery_worker_process.terminate()
    
    if celery_beat_process:
        print("Terminating Celery beat...")
        celery_beat_process.terminate()
    
    print("All processes terminated.")

def signal_handler(sig, frame):
    """Handle Ctrl+C signal."""
    print("\nCtrl+C detected. Cleaning up...")
    cleanup()
    sys.exit(0)

def run_django_server():
    """Run Django development server."""
    global server_process
    
    print("Starting Django development server...")
    server_process = subprocess.Popen(
        ['python', 'manage.py', 'runserver', '0.0.0.0:8000'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Start a thread to read and print server output
    from threading import Thread
    def print_output():
        for line in server_process.stdout:
            print(f"[Django] {line.strip()}")
    
    Thread(target=print_output, daemon=True).start()
    
    # Wait for server to start
    time.sleep(2)
    print("Django server running at http://localhost:8000/")

def run_celery_worker():
    """Run Celery worker."""
    global celery_worker_process
    
    print("Starting Celery worker...")
    celery_worker_process = subprocess.Popen(
        ['celery', '-A', 'healthcare', 'worker', '--loglevel=info'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Start a thread to read and print worker output
    from threading import Thread
    def print_output():
        for line in celery_worker_process.stdout:
            print(f"[Celery Worker] {line.strip()}")
    
    Thread(target=print_output, daemon=True).start()
    
    # Wait for worker to start
    time.sleep(2)
    print("Celery worker running.")


def check_redis():
    """Check if Redis is running."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("Redis is running.")
        return True
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        print("Please make sure Redis is installed and running.")
        return False

def main():
    """Main function to run all services."""
    # Register cleanup function to run on exit
    atexit.register(cleanup)
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Ensure we're in the project root directory
    if not os.path.exists('manage.py'):
        print("Error: This script must be run from the project root directory.")
        sys.exit(1)
    
    # Check if Redis is running
    if not check_redis():
        sys.exit(1)
    
    # Run Django server
    run_django_server()
    
    # Run Celery worker
    run_celery_worker()
    
    
    print("\nAll services are running. Press Ctrl+C to stop.")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == '__main__':
    main()
