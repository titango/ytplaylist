import os
import re
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
    file_name (str): The name of the file being checked (e.g., 'abc.mp3').
    download_dir (str): The directory where files are downloaded.

    Returns:
    bool: True if a duplicate file name exists, False otherwise.
    """
    file_path = os.path.join(download_dir, file_name.strip())
    if os.path.isfile(file_path):
        log_message(f'File <<{file_name}>> already exists, skipping.\n')
        return True
    log_message(f'No duplicate found for: {file_name}')
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
