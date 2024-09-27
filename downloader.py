import yt_dlp
import re
import os

def sanitize_filename(filename):
    # Replace any character that is not a letter, number, hyphen, or underscore with an underscore
    return re.sub(r'[^a-zA-Z0-9-_]', '_', filename)

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/temp_%(id)s.%(ext)s',  # Temporarily download with a safe name
    'quiet': True,
}



def download_yt_mp3_from_url(url):
    
    success = False
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_title = info['title']
            video_id = info['id']
            downloaded_temp_file = f"downloads/temp_{video_id}.mp3"
            sanitized_title = sanitize_filename(raw_title)
            final_audio_file = f"downloads/{sanitized_title}.mp3"
            if os.path.exists(downloaded_temp_file):
                os.rename(downloaded_temp_file, final_audio_file)
                print(f"Renamed file from {downloaded_temp_file} to {final_audio_file}")
                success = True
                return success, final_audio_file
   
    except Exception as e:
        return success, e