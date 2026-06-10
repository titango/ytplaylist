"""yt_dlp.py
This module provides functions to download YouTube videos and playlists
using yt-dlp only (no pytubefix required).
"""

import os
from yt_dlp import YoutubeDL
from tqdm import tqdm

from .file import (
    sanitize_filename,
    check_duplicate_name,
    log_message,
)

# Use a dictionary to store the progress bar state.
# This avoids the use of the 'global' keyword while maintaining shared state.
pbar_state = {"pbar": None}


def _make_gui_progress_hook(callback):
    """
    Create a yt-dlp progress hook that calls *callback(n, total)*.

    Used by the GUI to receive progress updates without polluting the
    module-level ``pbar_state`` or the ``tqdm``-based progress bar.
    """
    def hook(d):
        if d["status"] == "downloading":
            total = (
                d.get("total_bytes")
                or d.get("total_bytes_estimate")
                or 0
            )
            downloaded = d.get("downloaded_bytes", 0)
            callback(downloaded, total)
        elif d["status"] == "finished":
            total = (
                d.get("total_bytes")
                or d.get("total_bytes_estimate")
                or 0
            )
            callback(total, total)
    return hook


def progress_bar_hook(d):
    """
    Update the progress bar based on download status.
    """
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


def download_playlist_yt_dlp(
    download_dir,
    playlist_url,
    progress_callback=None,
    cancel_event=None,
):
    """
    Download every video in a playlist.

    Parameters
    ----------
    download_dir : str
        Directory to save downloaded files.
    playlist_url : str
        URL of the YouTube playlist.
    progress_callback : callable or None
        Optional ``(n, total)`` callback for per-video progress (GUI mode).
    cancel_event : threading.Event or None
        When set, stops processing remaining videos after the current one.
    """
    try:
        opts = {
            "proxy": "",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
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

        total = len(entries)

        for index, entry in enumerate(entries, start=1):
            if cancel_event and cancel_event.is_set():
                log_message(
                    "Download cancelled by user. "
                    "All remaining videos have been skipped."
                )
                break

            if entry is None:
                log_message(
                    f"Skipping video {index} of {total}: "
                    f"unavailable (yt-dlp returned no entry)"
                )
                continue

            video_url = entry.get("url")
            web_url = entry.get("webpage_url")

            if not video_url:
                log_message(
                    f"Skipping video {index} of {total}: "
                    f"no URL found in entry"
                )
                continue

            if not video_url.startswith("http"):
                video_url = (
                    f"https://www.youtube.com/watch?v={video_url}"
                )

            log_message(
                f"\nProcessing video {index} of {total} "
                f"{web_url}"
            )

            download_video_yt_dlp(
                video_url,
                download_dir,
                entry['title'],
                progress_callback=progress_callback,
                cancel_event=cancel_event,
            )

    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch all exceptions so a single bad video doesn't abort the playlist.
        log_message(
            f"Failed to process playlist {playlist_url}: {e}"
        )


def download_video_yt_dlp(url, download_dir, title=None, progress_callback=None, cancel_event=None):
    """
    Download a YouTube video's audio as MP3.

    Parameters
    ----------
    url : str
        The video URL to download.
    download_dir : str
        Directory to save the file.
    title : str or None
        Video title used for the filename.
    progress_callback : callable or None
        Optional ``(n, total)`` callback for per-video progress (GUI mode).
        When provided, the module-level ``tqdm`` progress bar is skipped.
    cancel_event : threading.Event or None
        When set before the download starts, the download is skipped.

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

        if cancel_event and cancel_event.is_set():
            log_message(
                "Download cancelled by user"
            )
            return None

        output_template = os.path.join(
            download_dir,
            f"{video_title}.%(ext)s"
        )

        # Choose the progress hook based on whether a GUI callback is active.
        # When no callback is provided, the default tqdm-based hook is used.
        if progress_callback:
            hooks = [_make_gui_progress_hook(progress_callback)]
        else:
            hooks = [progress_bar_hook]

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "progress_hooks": hooks,
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

    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch all exceptions so a single failed download doesn't abort the playlist.
        log_message(
            f"Failed to download {url}: {e}"
        )
        return None
