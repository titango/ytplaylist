"""Worker thread for GUI — runs downloads in the background.

Captures stdout/stderr so ``log_message()`` and yt-dlp output appear
in the GUI's log area without modifying ``lib/``.
"""

import sys
import threading
from queue import Queue
from lib.yt_dlp import download_playlist_yt_dlp


class _TeeStream:
    """
    A write-only stream that *forwards* every write to an original stream
    (preserving normal console output) while also queueing complete lines
    for the GUI.

    Handles both ``\\n``-terminated lines and ``\\r``-based progress
    updates (the latter overwrite the same terminal line, so only the
    final version is forwarded).
    """

    def __init__(self, original_stream, queue: Queue, msg_type: str):
        self._original = original_stream
        self._queue = queue
        self._msg_type = msg_type
        self._buffer = ""

    def write(self, text: str):
        """Write *text* to the original stream and forward complete lines to the queue."""
        # Forward to the original stream so terminal output is preserved.
        self._original.write(text)
        self._original.flush()

        # Buffer the text.
        self._buffer += text

        # Handle \r-based progress updates (e.g. yt-dlp's [download]
        # lines that overwrite the same terminal line).
        # Split on \r and keep only the most recent segment.
        if "\r" in self._buffer:
            segments = self._buffer.split("\r")
            self._buffer = segments[-1]

        # Handle \n-terminated lines.
        if "\n" in self._buffer:
            lines = self._buffer.split("\n")
            self._buffer = lines.pop()
            for line in lines:
                stripped = line.rstrip("\r")
                if stripped:
                    self._queue.put((self._msg_type, stripped))

    def flush(self):
        """Flush the original stream."""
        self._original.flush()


class DownloadWorker:
    """
    Runs the playlist download in a daemon thread.

    Sends the following tuples to *queue*:

    ``("log", text)``
        A log line captured from stdout/stderr.
    ``("progress", (n, total))``
        Per-video byte-level progress.
    ``("video_start", (index, total, title))``
        A new video is starting (for the counter label).
    ``("done", None)``
        Download completed successfully.
    ``("error", reason)``
        Download failed with an exception.
    """
    # pylint: disable=too-few-public-methods
    # A worker class is a single-purpose runner, not a utility bundle.

    def __init__(self, download_dir: str, playlist_url: str, queue: Queue,
                 cancel_event: threading.Event):
        self.download_dir = download_dir
        self.playlist_url = playlist_url
        self.queue = queue
        self.cancel_event = cancel_event
        self._thread: threading.Thread | None = None

    def start(self):
        """Launch the worker daemon thread."""
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="DownloadWorker")
        self._thread.start()

    def _on_progress(self, n: int, total: int):
        """Called by the ``progress_callback`` in ``lib/``."""
        self.queue.put(("progress", (n, total)))

    def _run(self):
        """Main work — called inside the daemon thread."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            sys.stdout = _TeeStream(old_stdout, self.queue, "log")
            sys.stderr = _TeeStream(old_stderr, self.queue, "log")

            download_playlist_yt_dlp(
                self.download_dir,
                self.playlist_url,
                progress_callback=self._on_progress,
                cancel_event=self.cancel_event,
            )

            # Check if we were cancelled.
            if self.cancel_event.is_set():
                self.queue.put(("log", "Download cancelled."))
            else:
                self.queue.put(("log", "All done! Download complete."))

            self.queue.put(("done", None))

        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.queue.put(("error", str(exc)))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
