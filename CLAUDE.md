# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run**: `python main.py` — downloads playlist configured in `config.json`
- **Lint**: `pylint $(git ls-files '*.py')` — CI runs pylint on push to `main`/`develop`
- **Test (unit)**: `pytest tests/ -v` — runs all unit tests under `tests/`
- **Test (single file)**: `pytest tests/test_file.py -v` — runs only file utility tests
- **Test (single function)**: `pytest tests/test_yt_dlp.py::TestDownloadPlaylist::test_skips_none_entries -v`
- **Smoke test**: `python test_yt.py` — quick connectivity test (fetches a single video's title via yt-dlp, requires network)
- **Lint**: `pylint $(git ls-files '*.py')` — CI runs pylint on push to `main`/`develop`
- **Setup**: `./setup.sh` — bootstraps pyenv 3.12 + venv + pip install
- **Install deps**: `pip install -r requirements.txt`

## Architecture

```
main.py          — Entry point. Reads config.json, calls lib/yt_dlp.
lib/yt_dlp.py    — Core logic: playlist iteration, yt-dlp wrapper, progress bar.
lib/file.py      — Utilities: filename sanitization, duplicate checking, logging.
test_yt.py       — Standalone smoke test (not pytest-based).
tests/
  __init__.py
  test_file.py    — Pytest tests for lib/file.py (filename sanitization, duplicates, logging).
  test_yt_dlp.py  — Pytest tests for lib/yt_dlp.py (playlist iteration, download, progress bar, mocked yt-dlp).
config.json      — User config: DOWNLOAD_DIR, YOUTUBE_PLAYLIST.
```

### Key design decisions

- **No CLI arguments** — everything is configured via `config.json` (`DOWNLOAD_DIR`, `YOUTUBE_PLAYLIST`).
- **Resilient per-video error handling** — both `download_playlist_yt_dlp()` and `download_video_yt_dlp()` catch broad exceptions so a single unavailable video (deleted, terminated account) doesn't abort the playlist. `None` entries in the playlist are logged and skipped.
- **Progress bar via module-level state** — `pbar_state` dict in `lib/yt_dlp.py` holds a `tqdm` instance shared across `progress_bar_hook()` calls. Avoids `global` keyword but is effectively module-level mutable state.
- **Android player client** — `extractor_args: {"youtube": {"player_client": ["android"]}}` is used for both playlist extraction and individual downloads to avoid bot detection / rate limiting. The playlist extraction also passes `"skip": ["authcheck"]` via `youtubetab` extractor args.
- **Logging is opt-in** — `IS_LOGGING = False` in `lib/file.py`. File logging to `./log/` is disabled by default; only console output is active.
- **Filename sanitization** — `sanitize_filename()` replaces path-unsafe characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) with `-` to prevent yt-dlp from creating unintended subdirectories.
- **Duplicate detection** — `check_duplicate_name()` checks if the target `.mp3` already exists in the download directory before starting a download.

### Error handling pattern

Both playlist and per-video functions use broad `except Exception` as a deliberate design choice — the project prioritizes completing the full playlist over surfacing individual failures. Errors are logged via `log_message()` and the download continues.

### Dependencies

- Python 3.12 (managed via pyenv + .python-version)
- `yt-dlp` (download + extraction), `tqdm` (progress bar), system `ffmpeg` (audio conversion via yt-dlp's FFmpegExtractAudio post-processor)
- `pytest` for unit tests (mock yt-dlp to avoid network access in tests)
