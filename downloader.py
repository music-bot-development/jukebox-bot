import re


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