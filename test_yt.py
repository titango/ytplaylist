"""Test module for downloading YouTube playlist info using yt_dlp."""
from yt_dlp import YoutubeDL

URL = "https://www.youtube.com/watch?v=4NeZegMB0kY"

OPTS = {
    "proxy": "",
    "no_warnings": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    },
    "quiet": False,
}

with YoutubeDL(OPTS) as ydl:
    info = ydl.extract_info(URL, download=False)

print(info['title'])
