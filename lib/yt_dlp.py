"""yt_dlp.py
This module provides functions to download YouTube videos and playlists
using yt-dlp only (no pytubefix required).
"""

import os
import json
# pylint: disable=import-self
# This imports the third-party "yt_dlp" package, not the current
# module "lib.yt_dlp" — pylint 4.x's name-matching heuristic flags
# it as a self-import despite the different package paths.
from yt_dlp import YoutubeDL
from tqdm import tqdm

from lib.file import (
    sanitize_filename,
    check_duplicate_name,
    log_message,
)

# Use a dictionary to store the progress bar state.
# This avoids the use of the 'global' keyword while maintaining shared state.
pbar_state = {"pbar": None}
def progress_bar_hook(d):
    if d["status"] == "downloading":
        if pbar_state["pbar"] is None:
            total = (
                d.get("total_bytes")
                or d.get("total_bytes_estimate")
                or 0
            )

            pbar_state["pbar"] = tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                desc="Downloading",
                leave=True,
            )

        downloaded = d.get("downloaded_bytes", 0)
        pbar_state["pbar"].n = downloaded
        pbar_state["pbar"].refresh()

    elif d["status"] == "finished":
        if pbar_state["pbar"]:
            pbar_state["pbar"].n = pbar_state["pbar"].total
            pbar_state["pbar"].refresh()
            pbar_state["pbar"].close()

            tqdm.write(
                f"Downloaded File Web: {d.get('filename', '')}"
            )

            pbar_state["pbar"] = None

def download_playlist_yt_dlp(download_dir, playlist_url):
    """
    Download every video in a playlist.
    """

    try:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            }
        }

        with YoutubeDL(opts) as ydl:
            playlist_info = ydl.extract_info(
                playlist_url,
                download=False,
            )

        entries = playlist_info.get("entries", [])
        # print(f"entries: {entries}")
        json_str = json.dumps(entries, indent=4)
        with open("sample.json", "w", encoding="utf-8") as f:
            f.write(json_str)

        total = len(entries)

        for index, entry in enumerate(entries, start=1):
            video_url = entry.get("url")

            if not video_url:
                continue

            if not video_url.startswith("http"):
                video_url = (
                    f"https://www.youtube.com/watch?v={video_url}"
                )

            log_message(
                f"\nProcessing video {index} of {total} "
                f"({video_url})"
            )

            download_video_yt_dlp(download_dir, video_url)

    except Exception as e:
        log_message(
            f"Failed to download playlist {playlist_url}: {e}"
        )

def download_video_yt_dlp(download_dir, video_url):
    """
    Download a single YouTube video.
    """
    try:
        ext = "mp3"
        opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': ext,
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        with YoutubeDL(opts) as ydl:
            ydl.download([video_url])

    except Exception as e:
        log_message(
            f"Failed to download {video_url}: {e}"
        )
