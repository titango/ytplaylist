from yt_dlp import YoutubeDL

url = "https://www.youtube.com/watch?v=4NeZegMB0kY"

opts = {
    "proxy": "",
    "no_warnings": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    },
    "quiet": False,
}

with YoutubeDL(opts) as ydl:
    info = ydl.extract_info(url, download=False)

print(info['title'])