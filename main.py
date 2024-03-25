import os
import subprocess
import json
from pytube import Playlist, YouTube
from pytube.exceptions import VideoUnavailable
from tqdm import tqdm

def on_progress(stream, chunk, bytes_remaining):
    progress_bar = tqdm(total=stream.filesize, unit='B', unit_scale=True, unit_divisor=1024)
    bytes_received = stream.filesize - bytes_remaining
    progress_bar.update(bytes_received)

def download_video(url, download_dir):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        stream = yt.streams.filter(only_audio=True)
        print(f'Downloading video: {url} - Title: {yt.title}')
        output_file = stream.first().download(output_path=download_dir)
        print(f'Downloaded successfully')
        return output_file
    except VideoUnavailable:
        print(f'Video {url} is unavailable, skipping.')
        return None

def convert_to_mp3(input_file, download_dir, ffmpeg_path):
    base, _ = os.path.splitext(input_file)
    mp3_file = base + '.mp3'
    print(f'Converting to MP3 file.....')
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
    print(f'MP3 file converted: {mp3_file}\n')

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

def main():
    config = load_config()
    download_dir = config['DOWNLOAD_DIR']
    youtube_playlist = config['YOUTUBE_PLAYLIST']
    ffmpeg_path = config.get('FFMPEG_PATH', '/usr/bin/ffmpeg')  # Default path if not specified

    playlist = Playlist(youtube_playlist)
    for url in playlist.video_urls:
        output_file = download_video(url, download_dir, itag)
        if output_file:
            convert_to_mp3(output_file, download_dir, ffmpeg_path)

if __name__ == "__main__":
    main()
