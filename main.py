"""Main file"""
import json
from lib.yt_dlp import download_playlist_yt_dlp

_version = "0.2.0"
def load_config():
    
    """
    Loads the configuration settings from a JSON file.

    Returns:
    dict: The configuration settings.
    """
    with open('config.json', 'r', encoding='utf-8') as config_file:
        return json.load(config_file)

def main():
    """ Main function"""
    config = load_config()
    download_dir = config['DOWNLOAD_DIR']
    youtube_playlist = config['YOUTUBE_PLAYLIST']
    ffmpeg_path = config.get('FFMPEG_PATH', '/usr/bin/ffmpeg')  # Default path if not specified

    if not download_dir or not youtube_playlist:
        print("Download directory and YouTube playlist must be specified in the config.")
        return
    download_playlist_yt_dlp(download_dir, youtube_playlist, ffmpeg_path)

if __name__ == "__main__":
    main()