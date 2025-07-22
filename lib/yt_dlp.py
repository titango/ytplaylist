"""yt_dlp.py
This module provides functions to download YouTube playlists using yt-dlp.
It includes functionality to sanitize filenames, check for duplicates,"""
import os
from yt_dlp import YoutubeDL
from pytubefix import Playlist
from lib.file import sanitize_filename, check_duplicate_name, convert_to_mp3, log_message


def download_playlist_yt_dlp(download_dir, youtube_playlist, ffmpeg_path):
    playlist = Playlist(youtube_playlist)
    for index, url in enumerate(playlist.video_urls, start=1):
        log_message(f'Processing video {index} of {len(playlist.video_urls)} ({url})')
        download_video_yt_dlp(url, download_dir)


def download_video_yt_dlp(url, download_dir):
    """
    Downloads a video from a given URL as audio using yt-dlp and saves it to the specified directory.
    Returns the path to the downloaded file, or None if unsuccessful.
    """
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            sanitized_title = sanitize_filename(info.get('title', 'audio'))
            ext = 'mp3'
            filename = f"{sanitized_title}.{ext}"
            file_path = os.path.join(download_dir, filename)
            if check_duplicate_name(filename, download_dir):
                log_message(f"Duplicate file detected: {filename}")
                return None
            log_message(f"Downloaded successfully: {file_path}")
            return file_path if os.path.exists(file_path) else None
    except Exception as e:
        log_message(f"Failed to download {url}: {e}")
        return None