# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-06-10
- **New GUI version** — full desktop application using Tkinter with the same feature set as the CLI.
- **CLI moved to `cli/` package** — `python -m cli.main` (legacy `python main.py` still works as a wrapper).
- **`gui/app.py`** — Tkinter main window with URL/directory fields, Browse button, Start/Cancel toggle, per-video progress bar, and log area.
- **`gui/worker.py`** — background `DownloadWorker` thread that communicates with the UI via a thread-safe `queue.Queue`, keeping the interface responsive during downloads.
- **`lib/yt_dlp.py` extended** — `download_playlist_yt_dlp()` and `download_video_yt_dlp()` now accept optional `progress_callback` and `cancel_event` parameters. Both default to `None`, preserving full backward compatibility with the CLI.
- **Cancel support** — GUI can cancel a download mid-playlist. The current video finishes, then all remaining videos are skipped cleanly.
- **Shared config** — both CLI and GUI use the same `config.json` at the project root. The GUI loads it on startup and saves it on start/close.
- **Removed `test_yt.py`** — manual smoke test superceded by the automated test suite and real GUI verification.
- **Removed `yarn.lock`** — unrelated to this Python project.
- **Updated README** with new project structure, GUI usage instructions, shared config docs, and WSL troubleshooting tips.

## [0.3.0] - 2026-06-06
- Fixed a crash where a single unavailable video in a playlist (e.g., terminated account) would abort the whole download run. Unavailable videos are now skipped and the rest of the playlist continues.
- Added logging for skipped videos, including the reason (`unavailable` / `no URL found in entry`).
- Fixed a bug where video titles containing `/` (e.g., `AA/BB/CC`) were being interpreted as directory paths by `yt-dlp`'s output template, creating unwanted subdirectories. Slashes (and other path-unsafe characters) are now converted to `-` in the on-disk filename.

## [0.2.1] - 2025-07-22
- Improved duplicate file detection logic for Unicode and edge cases
- Enhanced progress bar display for downloads; progress now remains visible after completion
- Refactored and clarified console/log messages for better user feedback
- Updated and cleaned up utility functions for file operations
- Minor bug fixes and code cleanup

## [0.2.0] - 2025-04-25
- Switched to `yt_dlp` for downloading videos to avoid YouTube error 400.
- Improved playlist parsing and reliability.
- Updated documentation and installation instructions.
- Added example `config.json` to help with configuration.
- Enhanced error handling and troubleshooting tips.

## [0.1.0] - 2024-12-10
- Initial release.
- Added YouTube playlist download functionality using `pytubefix`.
- Basic MP3 conversion using `ffmpeg`.
- Simple configuration via `config.json`