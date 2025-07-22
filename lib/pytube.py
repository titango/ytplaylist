"""Deprecated: Please use yt_dlp.py instead for downloading YouTube videos and playlists."""
import sys
from tqdm import tqdm
from pytubefix import YouTube, Playlist
from pytubefix.exceptions import VideoUnavailable

# Assuming these are custom utility functions defined elsewhere in the project
from lib.file import sanitize_filename, check_duplicate_name, log_message, convert_to_mp3
from lib.youtube_token import po_token_verifier

def download_video_pytube(url, download_dir):
    """
    Downloads a video from a given URL and saves it to the specified directory.

    Parameters:
    url (str): The URL of the video to download.
    download_dir (str): The directory to save the downloaded video.

    Returns:
    str or None: The path to the downloaded video file, or None if the download was unsuccessful.
    """
    try:
        yt = YouTube(url, on_progress_callback=on_progress, use_po_token=True,
                 po_token_verifier=po_token_verifier)   
        # Sanitize the filename before downloading
        sanitized_title = sanitize_filename(yt.title)    
        stream = yt.streams.filter(only_audio=True).first()
        if check_duplicate_name(sanitized_title + stream.default_filename.split('.')[-1], download_dir):
            return None
        log_message(f'Downloading video: {url}')
        log_message(f'Title: {yt.title}')
        output_file = stream.download(output_path=download_dir,
                                      filename=sanitized_title + '.' + stream.default_filename.split('.')[-1]
        )
        log_message('Downloaded successfully.')
        return output_file
    except VideoUnavailable:
        log_message(f'Video {url} is unavailable, skipping.')
        error_type, e, error_traceback = sys.exc_info()
        print(f'Failed with Error: {e}')
        return None
      
def download_playlist_pytube(download_dir, youtube_playlist, ffmpeg_path):
    playlist = Playlist(youtube_playlist)
    for index, url in enumerate(playlist.video_urls, start=1):
        log_message(f'Processing video {index} of {len(playlist.video_urls)} ({url})')
        output_file = download_video_pytube(url, download_dir)
        if output_file:
            convert_to_mp3(output_file, download_dir, ffmpeg_path)
            
def on_progress(stream, _chunk, bytes_remaining):
    """
    Updates the progress bar during a download operation.

    Parameters:
    stream (pytube.Stream): The stream being downloaded.
    chunk (bytes): The chunk of data that was just downloaded.
    bytes_remaining (int): The number of bytes still to be downloaded.
    """
    progress_bar = tqdm(total=stream.filesize, unit='B', unit_scale=True,
                        unit_divisor=1024, ncols=80)
    bytes_received = stream.filesize - bytes_remaining
    progress_bar.update(bytes_received)