import psutil

def cleanup_ffmpeg():
    "Helper function to kill any lingering FFmpeg processes."
    for proc in psutil.process_iter():
        if proc.name() == 'ffmpeg':
            proc.kill()
            proc.wait()
            print(f"Force killed lingering FFmpeg process: {proc.pid}")
