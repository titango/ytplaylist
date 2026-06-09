# lib/ — Core library

This directory contains the core logic shared between the CLI entry point and tests.

## Modules

### `__init__.py`
Empty package init — makes `lib` importable.

### `file.py` — Utilities
| Function | Signature | Description |
|----------|-----------|-------------|
| `sanitize_filename` | `(filename: str) -> str` | Replaces path-unsafe chars (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) with `-` so yt-dlp doesn't create unintended subdirectories. |
| `check_duplicate_name` | `(file_name: str, download_dir: str) -> bool` | Returns `True` if `file_name` (`.strip()`'d) already exists in `download_dir`. Used *before* starting a download. |
| `log_message` | `(message: str) -> None` | `print()`s to stdout. Optionally appends to a timestamped log file under `./log/` when `IS_LOGGING = True`. |

**Module-level state:** `IS_LOGGING = False`, `LOG_FILE_PATH` set at import time via `datetime.now()` — each import gets a new file (seconds granularity).

### `yt_dlp.py` — Download orchestration
| Function | Signature | Description |
|----------|-----------|-------------|
| `download_playlist_yt_dlp` | `(download_dir: str, playlist_url: str) -> None` | Extracts playlist entries via `YoutubeDL.extract_info`, iterates each entry, calls `download_video_yt_dlp` per valid entry. Handles `None` entries and missing URLs gracefully. |
| `download_video_yt_dlp` | `(url: str, download_dir: str, title: str \| None = None) -> str \| None` | Downloads a single video as 192 kbps MP3 via yt-dlp's `FFmpegExtractAudio` post-processor. Sanitizes title, checks for duplicates first. Returns the file path on success, `None` on skip/failure. |
| `progress_bar_hook` | `(d: dict) -> None` | yt-dlp progress hook. Creates a `tqdm` bar on first `downloading` status, updates bytes, closes on `finished`. |

**Module-level state:** `pbar_state = {"pbar": None}` — a dict holding the single `tqdm` instance. Not `global` but effectively module-level mutable state. Tests must reset `pbar_state["pbar"] = None` in `setup_method`.

## Key interactions

```
main.py
  └─ download_playlist_yt_dlp(download_dir, playlist_url)
       ├─ YoutubeDL.extract_info(playlist_url)       # playlist metadata
       ├─ for each entry:
       │    ├─ entry is None?       → log + skip
       │    ├─ entry has no url?    → log + skip
       │    └─ download_video_yt_dlp(video_url, download_dir, title)
       │         ├─ sanitize_filename(title)
       │         ├─ check_duplicate_name(filename, download_dir)  → skip if exists
       │         ├─ YoutubeDL.download([url])                     # + progress_bar_hook
       │         └─ os.path.exists(file_path)                     → return path or None
       └─ broad except Exception → log + continue
```

## yt-dlp configuration

**Playlist extraction** (in `download_playlist_yt_dlp`):
- `player_client: ["android"]` — avoids bot detection
- `skip: ["authcheck"]` via `youtubetab` extractor
- `ignoreerrors: True` — skips unavailable videos silently

**Per-video download** (in `download_video_yt_dlp`):
- `format: "bestaudio/best"`
- `postprocessors`: `FFmpegExtractAudio` → `mp3` at `192` kbps
- `progress_hooks: [progress_bar_hook]`
- Same android `player_client`

## Testing

Tests in `tests/test_file.py` and `tests/test_yt_dlp.py` use `unittest.mock` to avoid network/filesystem. Key fixtures and helpers:
- `tmp_path` — temp directory for duplicate checks
- `capsys` — stdout capture for log assertions
- `monkeypatch` — toggle `IS_LOGGING`, override `LOG_FILE_PATH`
- `_mock_ydl_context()` — `MagicMock` with proper `__enter__`/`__exit__` for `with YoutubeDL(...) as ydl:`
- `_make_entry(id, title, url)` — builds fake playlist entry dicts

## Error handling pattern

Both public functions use `except Exception` (broad catch). This is a deliberate trade-off: the project prioritizes completing the full playlist download over surfacing individual failures. Errors are logged and the download continues.
