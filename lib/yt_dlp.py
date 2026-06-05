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
            "proxy": "",
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtubetab": {
                    "skip": ["authcheck"]
                },
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

            download_video_yt_dlp(
                video_url,
                download_dir,
                entry['title']
            )

    except Exception as e:
        log_message(
            f"Failed to process playlist {playlist_url}: {e}"
        )

def download_video_yt_dlp(url, download_dir, title=None):
    """
    Download a YouTube video's audio as MP3.

    Returns:
        str | None: Path to downloaded file.
    """

    ext = "mp3"

    try:
        video_title = sanitize_filename(
            title
        )

        filename = f"{video_title}.{ext}"

        if check_duplicate_name(filename, download_dir):
            log_message(
                f"Skipping duplicate file: {filename}"
            )
            return None

        output_template = os.path.join(
            download_dir,
            f"{title}.%(ext)s"
        )

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_bar_hook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            },
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_path = os.path.join(
            download_dir,
            filename,
        )

        if os.path.exists(file_path):
            log_message(
                f"Downloaded successfully as MP3: {file_path}"
            )
            return file_path

        log_message(
            f"Download completed but file not found: {file_path}"
        )
        return None

    except Exception as e:
        log_message(
            f"Failed to download {url}: {e}"
        )
        return None

