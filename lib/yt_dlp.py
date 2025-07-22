"""yt_dlp.py
This module provides functions to download YouTube playlists using yt-dlp.
It includes functionality to sanitize filenames, check for duplicates,"""
import os
from lib.pytube import get_Youtube_name
from yt_dlp import YoutubeDL
from tqdm import tqdm
from pytubefix import Playlist
from lib.file import sanitize_filename, check_duplicate_name, log_message

pbar = None
def progress_bar_hook(d):
    global pbar
    if d['status'] == 'downloading':
        if pbar is None:
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            pbar = tqdm(total=total, unit='B', unit_scale=True, desc='Downloading', leave=True)
        downloaded = d.get('downloaded_bytes', 0)
        pbar.n = downloaded
        pbar.refresh()
    elif d['status'] == 'finished':
        if pbar:
            pbar.n = pbar.total
            pbar.refresh()
            pbar.close()
            tqdm.write(f"Downloaded File Web: {d.get('filename', '')}")  # This stays in the terminal
            pbar = None

def download_playlist_yt_dlp(download_dir, youtube_playlist):
    playlist = Playlist(youtube_playlist)
    for index, url in enumerate(playlist.video_urls, start=1):
        log_message(f'\nProcessing video {index} of {len(playlist.video_urls)} ({url})')
        download_video_yt_dlp(url, download_dir)


def download_video_yt_dlp(url, download_dir):
    """
    Downloads a video from a given URL as audio using yt-dlp and saves it to the specified directory.
    Returns the path to the downloaded file, or None if unsuccessful.
    """
    ext = 'mp3'
    yt = get_Youtube_name(url, download_dir)
    if not check_duplicate_name(sanitize_filename(yt.title) + f".{ext}", download_dir):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(download_dir, sanitize_filename(yt.title) + '.%(ext)s'),
                'quiet': True,
                'progress_hooks': [progress_bar_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                sanitized_title = sanitize_filename(info.get('title', 'audio'))
                filename = f"{sanitized_title}.{ext}"
                file_path = os.path.join(download_dir, filename)
                log_message(f"Downloaded successfully as MP3: {file_path}")
                return file_path if os.path.exists(file_path) else None
        except Exception as e:
            log_message(f"Failed to download {url}: {e}")
            return None