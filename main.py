import os
from pytube import Playlist, YouTube
from pytube.exceptions import VideoUnavailable
from tqdm import tqdm
from dotenv import load_dotenv
import subprocess

def on_progress(stream, chunk, bytes_remaining):
    progress_bar = tqdm(total=stream.filesize, unit='B', unit_scale=True, unit_divisor=1024)
    bytes_received = stream.filesize - bytes_remaining
    progress_bar.update(bytes_received)
  
load_dotenv()
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR')
YOUTUBE_PLAYLIST = os.getenv('YOUTUBE_PLAYLIST')
ITAG = 141

p = Playlist(YOUTUBE_PLAYLIST)
for url in p.video_urls:
  try:
    yt = YouTube(
      url,
      on_progress_callback=on_progress
    )
  except(VideoUnavailable):
    print(f'Video {url} is unavaialable, skipping.')
  else:
    stream = yt.streams.filter(only_audio=True)
    audio_stream = stream.get_by_itag(ITAG)
    print(f'Downloading video: {url} - Title: {yt.title}')
    output_file =stream.first().download(output_path=DOWNLOAD_DIR)
    print(f'Downloaded successfully')
    
    # Convert the downloaded audio file to MP3
    base, ext = os.path.splitext(output_file)
    mp3_file = base + '.mp3'

    print(f'Converting to MP3 file.....')
    downloaded_audio_file = os.path.join(DOWNLOAD_DIR, os.path.basename(output_file.strip()))
    
    # Suppress FFmpeg output
    ffmpeg_command = [
      "ffmpeg",
      "-y",  # Overwrite output file without asking
      "-i", downloaded_audio_file,
      "-codec:a", "libmp3lame",
      "-b:a", "320k",  # Set audio bitrate to 320kbps
      mp3_file
    ]
    subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    os.remove(downloaded_audio_file)
    print(f'MP3 file converted: {mp3_file}\n')
