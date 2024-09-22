import os
import psutil
import glob
import time

def cleanup_ffmpeg():
    "Helper function to kill any lingering FFmpeg processes."
    for proc in psutil.process_iter():
        if proc.name() == 'ffmpeg':
            proc.kill()
            proc.wait()
            print(f"Force killed lingering FFmpeg process: {proc.pid}")

def cleanup_download_folder():
    
    retries = 6
    delay = 2
    
    folder_path = 'downloads/'
    files = glob.glob(os.path.join(folder_path, "*"))
    
    for file in files:
        for attempt in range(retries):
            try:
                print(file)
                os.remove(file)
                print(f"Deleted: {file}")
                break  # Exit retry loop once the file is successfully deleted
            except Exception as e:
                print(f"Error deleting {file}: {e}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)  # Wait before retrying
                else:
                    print(f"Failed to delete {file} after {retries} attempts.")