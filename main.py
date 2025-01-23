"""Main file"""
import sys
import os  # noqa: D100
import subprocess
import json
import re
from datetime import datetime
from pytubefix import YouTube, Playlist
from pytubefix.exceptions import VideoUnavailable
from tqdm import tqdm
from typing import Tuple

# Create a log directory if it doesn't exist
IS_LOGGING = False
LOG_DIR = './log'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Generate a log file name with the current datetime
LOG_FILE_NAME = datetime.now().strftime('log_%Y-%m-%d_%H:%M:%S') + '.txt'
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)

def sanitize_filename(filename):
    """
    Sanitize filename by removing or replacing characters that are not valid in file paths.
    """
    # Replace slashes with hyphens and remove other potentially problematic characters
    return re.sub(r'[/\\:*?"<>|]', '-', filename)

def log_message(message):
    """
    Logs a message to both the console and a log file if logging is enabled.

    Parameters:
    message (str): The message to be logged.
    """
    print(message)
    if IS_LOGGING:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
            log_file.write(message + '\n')

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

def check_duplicate_name(file_name, download_dir):
    """
    Checks if a file with the same name already exists in the download directory.

    Parameters:
    file_name (str): The name of the file being checked.
    download_dir (str): The directory where files are downloaded.

    Returns:
    bool: True if a duplicate file name exists, False otherwise.
    """
    file_name_without_extension = os.path.splitext(file_name)[0]
    for existing_file_name in os.listdir(download_dir):
        existing_file_name_without_extension = os.path.splitext(existing_file_name)[0]
        if file_name_without_extension in existing_file_name_without_extension:
            log_message(f'File <<{file_name}>> already exists, skipping.\n')
            return True
    return False

def download_video(url, download_dir):
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

def convert_to_mp3(input_file, download_dir, ffmpeg_path):
    """
    Converts a downloaded video file to MP3 format using ffmpeg.

    Parameters:
    input_file (str): The path to the downloaded video file.
    download_dir (str): The directory where the MP3 file will be saved.
    ffmpeg_path (str): The path to the ffmpeg executable.

    Returns:
    None
    """
    base, _ = os.path.splitext(input_file)
    mp3_file = base + '.mp3'
    log_message('Converting to MP3 file.....')
    downloaded_audio_file = os.path.join(download_dir, os.path.basename(input_file.strip()))

    ffmpeg_command = [
      ffmpeg_path,
      "-y",  # Overwrite output file without asking
      "-i", downloaded_audio_file,
      "-codec:a", "libmp3lame",
      "-b:a", "320k",  # Set audio bitrate to 320kbps
      mp3_file
    ]
    subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
    os.remove(downloaded_audio_file)
    log_message(f'MP3 file converted to {mp3_file}\n')

def load_config():
    
    """
    Loads the configuration settings from a JSON file.

    Returns:
    dict: The configuration settings.
    """
    with open('config.json', 'r', encoding='utf-8') as config_file:
        return json.load(config_file)
def po_token_verifier() -> Tuple[str, str]:
    """
    Verifies and returns YouTube visitor data and PO token.

    Returns:
        Tuple[str, str]: A tuple containing visitor data and PO token.
    """
    token_object = generate_youtube_token()
    return token_object["visitorData"], token_object["poToken"]


def generate_youtube_token() -> dict:
    """
    Generates a YouTube authentication token by executing a Node.js script.

    Returns:
        dict: A dictionary containing visitor data and PO token.
    """
    log_message("Generating YouTube token")
    result = subprocess.run(
        ["node", "youtube-token-generator.js"],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(result.stdout)
    log_message(f"Result: {data}")
    return data

def main():
    """ Main function"""
    config = load_config()
    download_dir = config['DOWNLOAD_DIR']
    youtube_playlist = config['YOUTUBE_PLAYLIST']
    ffmpeg_path = config.get('FFMPEG_PATH', '/usr/bin/ffmpeg')  # Default path if not specified

    playlist = Playlist(youtube_playlist)
    for index, url in enumerate(playlist.video_urls, start=1):
        log_message(f'Processing video {index} of {len(playlist.video_urls)} ({url})')
        output_file = download_video(url, download_dir)
        if output_file:
            convert_to_mp3(output_file, download_dir, ffmpeg_path)

if __name__ == "__main__":
    main()
