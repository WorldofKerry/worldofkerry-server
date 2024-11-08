import threading
import time
from datetime import datetime, timedelta

# Function to delete files older than 60 minutes
def delete_old_files():
    while True:
        # Calculate the time 60 minutes ago
        time_threshold = datetime.now() - timedelta(minutes=60)

        # Query to find files older than 60 minutes
        for file in fs.find({"uploadDate": {"$lt": time_threshold}}):
            # Delete the file from GridFS
            fs.delete(file._id)
            print(f"Deleted file: {file.filename} (ID: {file._id})")

        # Sleep for 60 seconds before checking again
        time.sleep(60)

# Start the cleanup task in the background
def start_cleanup_task():
    cleanup_thread = threading.Thread(target=delete_old_files, daemon=True)
    cleanup_thread.start()

# Start the cleanup task when the Flask app starts
@app.before_first_request
def before_first_request():
    start_cleanup_task()
