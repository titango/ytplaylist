"""Tests for lib/yt_dlp.py.

Uses mocking to avoid network access and real filesystem side effects.
"""
import os
from unittest.mock import patch, MagicMock

from lib.yt_dlp import (
    download_playlist_yt_dlp,
    download_video_yt_dlp,
    progress_bar_hook,
    pbar_state,
)


def _mock_ydl_context():
    """Return a MagicMock configured to act as a proper context manager.

    The code under test uses ``with YoutubeDL(opts) as ydl:``, so the
    object returned by ``YoutubeDL()`` must have ``__enter__`` return
    *itself*, and ``__exit__`` must return False so real exceptions are
    not swallowed.
    """
    m = MagicMock()
    m.__enter__.return_value = m
    m.__exit__.return_value = False
    return m


def _make_entry(entry_id, title, url=None):
    """Build a fake playlist entry dict for testing."""
    return {
        "id": entry_id,
        "title": title,
        "url": url or f"https://www.youtube.com/watch?v={entry_id}",
        "webpage_url": f"https://www.youtube.com/watch?v={entry_id}",
    }


# ---------------------------------------------------------------------------
# progress_bar_hook
# ---------------------------------------------------------------------------


class TestProgressBarHook:
    """Tests for the module-level progress bar hook."""

    def setup_method(self):
        """Reset pbar_state before each test."""
        if pbar_state["pbar"] is not None:
            pbar_state["pbar"].close()
            pbar_state["pbar"] = None

    def test_downloading_creates_and_updates_progress_bar(self):
        """Should create a new tqdm bar and set downloaded bytes."""
        hook_data = {
            "status": "downloading",
            "total_bytes": 1000,
            "downloaded_bytes": 250,
        }

        with patch("lib.yt_dlp.tqdm") as mock_tqdm:
            mock_instance = MagicMock()
            mock_tqdm.return_value = mock_instance

            progress_bar_hook(hook_data)

            mock_tqdm.assert_called_once_with(
                total=1000, unit="B", unit_scale=True, desc="Downloading", leave=True
            )
            assert pbar_state["pbar"] is mock_instance
            mock_instance.refresh.assert_called_once()

    def test_downloading_estimates_total(self):
        """Should use total_bytes_estimate when total_bytes is absent."""
        hook_data = {
            "status": "downloading",
            "total_bytes_estimate": 500,
            "downloaded_bytes": 100,
        }

        with patch("lib.yt_dlp.tqdm") as mock_tqdm:
            mock_instance = MagicMock()
            mock_tqdm.return_value = mock_instance

            progress_bar_hook(hook_data)

            mock_tqdm.assert_called_once_with(
                total=500, unit="B", unit_scale=True, desc="Downloading", leave=True
            )

    def test_downloading_falls_back_to_zero(self):
        """Should default to total=0 when no size info is available."""
        hook_data = {
            "status": "downloading",
            "downloaded_bytes": 50,
        }

        with patch("lib.yt_dlp.tqdm") as mock_tqdm:
            mock_instance = MagicMock()
            mock_tqdm.return_value = mock_instance

            progress_bar_hook(hook_data)

            mock_tqdm.assert_called_once_with(
                total=0, unit="B", unit_scale=True, desc="Downloading", leave=True
            )

    def test_finished_closes_bar_and_resets_state(self):
        """Should mark bar as complete, close it, and clear pbar_state."""
        mock_instance = MagicMock()
        mock_instance.total = 1000
        pbar_state["pbar"] = mock_instance

        hook_data = {
            "status": "finished",
            "filename": "/tmp/song.mp3",
        }

        progress_bar_hook(hook_data)

        assert mock_instance.n == 1000
        mock_instance.refresh.assert_called_once()
        mock_instance.close.assert_called_once()
        assert pbar_state["pbar"] is None

    def test_finished_with_no_bar_is_noop(self):
        """Should not crash when finished is called with no active bar."""
        pbar_state["pbar"] = None
        progress_bar_hook({"status": "finished"})


# ---------------------------------------------------------------------------
# download_playlist_yt_dlp
# ---------------------------------------------------------------------------


class TestDownloadPlaylist:
    """Tests for the playlist-level download orchestrator."""

    def test_downloads_all_valid_entries(self):
        """Should call download_video_yt_dlp for every valid entry."""
        entries = [
            _make_entry("a1", "First Video"),
            _make_entry("b2", "Second Video"),
            _make_entry("c3", "Third Video"),
        ]

        mock_ydl = _mock_ydl_context()
        mock_ydl.extract_info.return_value = {"entries": entries}

        with patch("lib.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with patch("lib.yt_dlp.download_video_yt_dlp") as mock_dl:
                download_playlist_yt_dlp("/tmp/dl", "https://example.com/pl")

                assert mock_dl.call_count == 3
                mock_dl.assert_any_call(
                    "https://www.youtube.com/watch?v=a1", "/tmp/dl", "First Video",
                    progress_callback=None, cancel_event=None,
                )

    def test_skips_none_entries(self):
        """Should skip None entries (unavailable videos) without crashing."""
        entries = [_make_entry("a1", "Valid"), None, _make_entry("c3", "Also Valid")]

        mock_ydl = _mock_ydl_context()
        mock_ydl.extract_info.return_value = {"entries": entries}

        with patch("lib.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with patch("lib.yt_dlp.download_video_yt_dlp") as mock_dl:
                download_playlist_yt_dlp("/tmp/dl", "https://example.com/pl")

                assert mock_dl.call_count == 2

    def test_skips_entries_without_url(self):
        """Should skip entries that lack a 'url' key."""
        bad_entry = {"id": "b2", "title": "No URL", "webpage_url": "..."}
        good_entry = _make_entry("c3", "Good")
        entries = [bad_entry, good_entry]

        mock_ydl = _mock_ydl_context()
        mock_ydl.extract_info.return_value = {"entries": entries}

        with patch("lib.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with patch("lib.yt_dlp.download_video_yt_dlp") as mock_dl:
                download_playlist_yt_dlp("/tmp/dl", "https://example.com/pl")

                assert mock_dl.call_count == 1

    def test_converts_short_url_to_full_url(self):
        """Should prefix non-http URLs with the full YouTube watch URL."""
        entries = [_make_entry("d4", "Short URL", url="d4")]

        mock_ydl = _mock_ydl_context()
        mock_ydl.extract_info.return_value = {"entries": entries}

        with patch("lib.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with patch("lib.yt_dlp.download_video_yt_dlp") as mock_dl:
                download_playlist_yt_dlp("/tmp/dl", "https://example.com/pl")

                mock_dl.assert_called_once_with(
                    "https://www.youtube.com/watch?v=d4", "/tmp/dl", "Short URL",
                    progress_callback=None, cancel_event=None,
                )

    def test_catches_extract_info_exception(self):
        """Should catch and log an exception from extract_info instead of crashing."""
        mock_ydl = _mock_ydl_context()
        mock_ydl.extract_info.side_effect = Exception("Network error")

        with patch("lib.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with patch("lib.yt_dlp.log_message") as mock_log:
                download_playlist_yt_dlp("/tmp/dl", "https://example.com/pl")
                mock_log.assert_called_once()
                assert "Network error" in mock_log.call_args[0][0]

    def test_handles_empty_playlist(self):
        """Should not attempt any downloads when the playlist has no entries."""
        mock_ydl = _mock_ydl_context()
        mock_ydl.extract_info.return_value = {"entries": []}

        with patch("lib.yt_dlp.YoutubeDL", return_value=mock_ydl):
            with patch("lib.yt_dlp.download_video_yt_dlp") as mock_dl:
                download_playlist_yt_dlp("/tmp/dl", "https://example.com/pl")
                mock_dl.assert_not_called()


# ---------------------------------------------------------------------------
# download_video_yt_dlp
# ---------------------------------------------------------------------------


class TestDownloadVideo:
    """Tests for the single-video download function."""

    def test_downloads_successfully(self):
        """Happy path: should download and return the file path."""
        with patch("lib.yt_dlp.sanitize_filename", return_value="My Song"):
            with patch("lib.yt_dlp.check_duplicate_name", return_value=False):
                with patch("lib.yt_dlp.YoutubeDL", return_value=_mock_ydl_context()):
                    with patch("os.path.exists", return_value=True):
                        result = download_video_yt_dlp(
                            "https://youtu.be/abc", "/music", "My Song"
                        )

        assert result == os.path.join("/music", "My Song.mp3")

    def test_skips_duplicate(self):
        """Should skip download when check_duplicate_name returns True."""
        with patch("lib.yt_dlp.sanitize_filename", return_value="My Song"):
            with patch("lib.yt_dlp.check_duplicate_name", return_value=True):
                with patch("lib.yt_dlp.YoutubeDL") as mock_ydl_cls:
                    result = download_video_yt_dlp(
                        "https://youtu.be/abc", "/music", "My Song"
                    )

        assert result is None
        mock_ydl_cls.assert_not_called()

    def test_reports_file_not_found_after_download(self):
        """Should return None and log a warning when the file is missing post-download."""
        with patch("lib.yt_dlp.sanitize_filename", return_value="My Song"):
            with patch("lib.yt_dlp.check_duplicate_name", return_value=False):
                with patch("lib.yt_dlp.YoutubeDL", return_value=_mock_ydl_context()):
                    with patch("os.path.exists", return_value=False):
                        with patch("lib.yt_dlp.log_message") as mock_log:
                            result = download_video_yt_dlp(
                                "https://youtu.be/abc", "/music", "My Song"
                            )

        assert result is None
        messages = [call[0][0] for call in mock_log.call_args_list]
        assert any("file not found" in m.lower() for m in messages)

    def test_catches_download_exception(self):
        """Should catch and log an exception from yt-dlp instead of crashing."""
        mock_ydl = _mock_ydl_context()
        mock_ydl.download.side_effect = Exception("DL failed")

        with patch("lib.yt_dlp.sanitize_filename", return_value="My Song"):
            with patch("lib.yt_dlp.check_duplicate_name", return_value=False):
                with patch("lib.yt_dlp.YoutubeDL", return_value=mock_ydl):
                    with patch("lib.yt_dlp.log_message") as mock_log:
                        result = download_video_yt_dlp(
                            "https://youtu.be/abc", "/music", "My Song"
                        )

        assert result is None
        assert any("DL failed" in call[0][0] for call in mock_log.call_args_list)

    def test_passes_correct_options_to_ydl(self):
        """Should pass the expected yt-dlp options (format, codec, quality)."""
        with patch("lib.yt_dlp.sanitize_filename", return_value="My Song"):
            with patch("lib.yt_dlp.check_duplicate_name", return_value=False):
                with patch("lib.yt_dlp.YoutubeDL") as mock_ydl_cls:
                    with patch("os.path.exists", return_value=True):
                        download_video_yt_dlp(
                            "https://youtu.be/abc", "/music", "My Song"
                        )

        passed_opts = mock_ydl_cls.call_args[0][0]
        assert passed_opts["format"] == "bestaudio/best"
        assert passed_opts["postprocessors"][0]["key"] == "FFmpegExtractAudio"
        assert passed_opts["postprocessors"][0]["preferredcodec"] == "mp3"
        assert passed_opts["postprocessors"][0]["preferredquality"] == "192"
        assert "outtmpl" in passed_opts
