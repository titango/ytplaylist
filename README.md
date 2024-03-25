### Ytplaylist - Download and convert YouTube playlist to MP3

<img src="images/logo.png" width="250">

Python script to download a YouTube playlist and convert it to MP3.

# Installation
1. Clone the repository to your local machine.
2. Navigate to the cloned repository's directory.
3. Run `setup.sh` to set up the Python environment and install the necessary dependencies.
4. Edit the `config.json` file to specify your `DOWNLOAD_DIR`, `YOUTUBE_PLAYLIST`, and `FFMPEG_PATH` according to your system setup.

# Usage
Run `python main.py` after configuring the `config` file

![console](images/console.png)

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
- `ffmpeg` for converting videos to MP3 format.

# Contributing

Feel free to fork the repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

# License

The MIT License (MIT)
Copyright © 2024

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.




