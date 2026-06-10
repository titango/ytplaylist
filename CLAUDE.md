# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **CLI**: `python -m cli.main` — downloads playlist configured in `config.json`
- **GUI**: `python -m gui.app` — launches the Tkinter GUI version (uses same `config.json`)
- **Setup from scratch**: `./setup.sh` then `source venv/bin/activate && pip install -r requirements.txt`
- **Install/update deps**: `pip install -r requirements.txt`
- **Lint**: `pylint $(git ls-files '*.py')` — CI runs this on push to `main`/`develop` (see `.github/workflows/pylint.yml`)
- **Test (all)**: `pytest tests/ -v`
- **Test (single file)**: `pytest tests/test_file.py -v`
- **Test (single function)**: `pytest tests/test_yt_dlp.py::TestDownloadPlaylist::test_skips_none_entries -v`

## Project structure

```
cli/
  main.py            — CLI entry point. Reads config.json, delegates to lib/yt_dlp.
gui/
  __init__.py        — Empty package init.
  app.py             — Tkinter GUI main window (reads/writes config.json).
  worker.py          — Background thread for downloads (Queue + threading).
lib/
  __init__.py        — Empty package init.
  yt_dlp.py          — Playlist iteration, per-video yt-dlp download, tqdm progress bar.
  file.py            — Filename sanitization, duplicate checking, logging.
tests/
  test_file.py       — Pytest tests for lib/file.py (sanitize, duplicate, log).
  test_yt_dlp.py     — Pytest tests for lib/yt_dlp.py (playlist, download, progress bar, mocked yt-dlp).
config.json          — Shared config: DOWNLOAD_DIR, YOUTUBE_PLAYLIST (CLI + GUI).
```

## Architecture & design decisions

- **Config-driven, no CLI args** — everything comes from `config.json` (`DOWNLOAD_DIR`, `YOUTUBE_PLAYLIST`).
- **Resilient per-video error handling** — both `download_playlist_yt_dlp()` and `download_video_yt_dlp()` catch broad `Exception` so a single unavailable video (deleted, terminated account) doesn't abort the playlist. `None` entries are logged and skipped.
- **Module-level progress bar state** — `pbar_state` dict holds a `tqdm` instance shared across `progress_bar_hook()` calls. This avoids the `global` keyword but is effectively module-level mutable state. Tests must reset `pbar_state["pbar"]` in `setup_method`.
- **Shared config** — both CLI and GUI use the same `config.json` at the project root. The GUI loads it on startup and saves it when starting a download or closing the window.
- **GUI progress via callback** — `lib/yt_dlp.py` accepts optional `progress_callback(n, total)` and `cancel_event` parameters. When provided, the GUI receives progress without polling `pbar_state`. Both default to `None` so CLI mode is unchanged.
- **Android player client** — `extractor_args: {"youtube": {"player_client": ["android"]}}` for both extraction and downloads to avoid bot detection / rate limiting. Playlist extraction also passes `"skip": ["authcheck"]` via `youtubetab` extractor args.
- **Logging is opt-in** — `IS_LOGGING = False` in `lib/file.py`. File logging to `./log/` is disabled by default; only `print()` to console is active. The log file path includes seconds, so each run creates a new file.
- **Filename sanitization** — `sanitize_filename()` replaces path-unsafe characters (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) with `-` to prevent yt-dlp from creating unintended subdirectories.
- **Duplicate detection** — `check_duplicate_name()` checks if the target `.mp3` already exists in `download_dir` *before* starting a download. Filename is `.strip()`'d before comparison.
- **Working directory** — both CLI and GUI should be run from the project root directory:
  `cd /home/tanngo/projects/ytplaylist && python -m cli.main`

## Testing patterns

- Tests use `unittest.mock` entirely — no network access or real filesystem side effects.
- Playlist tests use `_mock_ydl_context()` helper that returns a `MagicMock` with proper `__enter__`/`__exit__` for Python context manager protocol.
- Entry factory: `_make_entry(id, title, url=None)` builds fake playlist entry dicts.
- Tests for `check_duplicate_name` use pytest `tmp_path` fixture to avoid real disk writes.
- Tests for `log_message` use `capsys` fixture for stdout capture and `monkeypatch` to toggle `IS_LOGGING`.

## Dependencies

- Python 3.12 (managed via pyenv + `.python-version`)
- `yt-dlp` (download + extraction), `tqdm` (progress bar), system `ffmpeg` (audio conversion via yt-dlp's `FFmpegExtractAudio` post-processor), `pytest`
