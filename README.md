### Download and convert YouTube playlist to MP3

This is a simple Python script to download a YouTube playlist and convert it to MP3.

# Installation
1. Clone the repository to your local machine.
2. Navigate to the cloned repository's directory.
3. Run `setup.sh` to set up the Python environment and install the necessary dependencies.
4. Copy `env_template` to a new file named `.env`.
5. Edit the `.env` file to specify your `DOWNLOAD_DIR`, `YOUTUBE_PLAYLIST`, and `FFMPEG_PATH` according to your system setup.

# Usage
Run `python main.py` after configuring the `.env` file

# Configuration

- `DOWNLOAD_DIR`: The directory where the downloaded YouTube videos will be stored.
- `YOUTUBE_PLAYLIST`: The URL of the YouTube playlist you wish to download.
- `FFMPEG_PATH`: The path to your FFMPEG executable. This is used for converting videos to MP3.

# Features

- Downloads videos from a specified YouTube playlist.
- Converts the downloaded videos to MP3 format.
- Saves the MP3 files to the specified download directory.

# Requirements

- Python 3.6 or higher
- `pytube` for downloading videos from YouTube.
- `ffmpeg` for converting videos to MP3 format.
- `dotenv` for loading environment variables from the `.env` file.

# Contributing

Feel free to fork the repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

# License

This project is licensed under the MIT License - see the LICENSE file for details.




