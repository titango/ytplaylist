# Changelog

All notable changes to this project will be documented in this file.

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