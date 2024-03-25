import os
import subprocess
import json
from pytube import Playlist, YouTube
from pytube.exceptions import VideoUnavailable
from tqdm import tqdm
from datetime import datetime

# Create a log directory if it doesn't exist
log_dir = './log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Generate a log file name with the current datetime
log_file_name = datetime.now().strftime('log_%Y-%m-%d_%H:%M:%S') + '.txt'
log_file_path = os.path.join(log_dir, log_file_name)

# Function to log messages both to console and log file
def log_message(message):
    print(message)
    with open(log_file_path, 'a') as log_file:
        log_file.write(message + '\n')

def on_progress(stream, chunk, bytes_remaining):
    progress_bar = tqdm(total=stream.filesize, unit='B', unit_scale=True, unit_divisor=1024, ncols=80)
    bytes_received = stream.filesize - bytes_remaining
    progress_bar.update(bytes_received)

def download_video(url, download_dir):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        stream = yt.streams.filter(only_audio=True)
        log_message(f'Downloading video: {url}')
        log_message(f'Title: {yt.title}')
        output_file = stream.first().download(output_path=download_dir)
        log_message(f'Downloaded successfully.')
        return output_file
    except VideoUnavailable:
        log_message(f'Video {url} is unavailable, skipping.')
        return None

def convert_to_mp3(input_file, download_dir, ffmpeg_path):
    base, _ = os.path.splitext(input_file)
    mp3_file = base + '.mp3'
    log_message(f'Converting to MP3 file.....')
    downloaded_audio_file = os.path.join(download_dir, os.path.basename(input_file.strip()))
    
    ffmpeg_command = [
      ffmpeg_path,
      "-y",  # Overwrite output file without asking
      "-i", downloaded_audio_file,
      "-codec:a", "libmp3lame",
      "-b:a", "320k",  # Set audio bitrate to 320kbps
      mp3_file
    ]
    subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    os.remove(downloaded_audio_file)
    log_message(f'MP3 file converted to {mp3_file}\n')

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

def main():
    config = load_config()
    download_dir = config['DOWNLOAD_DIR']
    youtube_playlist = config['YOUTUBE_PLAYLIST']
    ffmpeg_path = config.get('FFMPEG_PATH', '/usr/bin/ffmpeg')  # Default path if not specified

    playlist = Playlist(youtube_playlist)
    for index, url in enumerate(playlist.video_urls, start=1):
        log_message(f'Processing video {index} of {len(playlist.video_urls)}')
        output_file = download_video(url, download_dir)
        if output_file:
            convert_to_mp3(output_file, download_dir, ffmpeg_path)

if __name__ == "__main__":
    main()
