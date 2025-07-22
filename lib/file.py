"""Utility functions for file operations"""
import os
import re
import subprocess
from datetime import datetime

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