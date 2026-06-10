"""GUI main window — YouTube Playlist Downloader.

Uses Tkinter (stdlib) with a background worker thread so the UI stays
responsive during downloads.
"""

import json
import os
import threading
from queue import Queue, Empty
from tkinter import (
    Tk,
    ttk,
    StringVar,
    filedialog,
    scrolledtext,
    messagebox,
)

# Shared config file at the project root (same file used by CLI).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

from gui.worker import DownloadWorker  # noqa: E402 (path laid before import)


class PlaylistDownloaderApp(Tk):
    """Main Tkinter window for the YouTube playlist downloader."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self.title("YouTube Playlist Downloader")
        self.geometry("700x600")
        self.minsize(600, 450)

        self._worker: DownloadWorker | None = None
        self._cancel_event: threading.Event | None = None
        self._queue: Queue | None = None
        self._polling = False

        self._build_ui()
        self._load_config()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # --- Playlist URL row ---
        ttk.Label(self, text="Playlist URL:").grid(
            row=0, column=0, padx=(10, 2), pady=(10, 2), sticky="e"
        )
        self._url_var = StringVar()
        self._url_entry = ttk.Entry(self, textvariable=self._url_var, width=70)
        self._url_entry.grid(row=0, column=1, padx=(2, 10), pady=(10, 2), sticky="ew")

        # --- Download directory row ---
        ttk.Label(self, text="Download to:").grid(
            row=1, column=0, padx=(10, 2), pady=2, sticky="e"
        )
        self._dir_var = StringVar()
        self._dir_entry = ttk.Entry(self, textvariable=self._dir_var, width=70)
        self._dir_entry.grid(row=1, column=1, padx=(2, 2), pady=2, sticky="ew")
        self._browse_btn = ttk.Button(
            self, text="Browse", command=self._browse_directory
        )
        self._browse_btn.grid(row=1, column=2, padx=(0, 10), pady=2)

        # --- Start / Cancel button ---
        self._action_btn = ttk.Button(
            self, text="Start Download", command=self._toggle_download
        )
        self._action_btn.grid(row=2, column=0, columnspan=3, pady=(8, 4))

        # --- Video counter + title ---
        self._video_label = ttk.Label(self, text="Video: -- of --")
        self._video_label.grid(row=3, column=0, columnspan=3, padx=10, sticky="w")

        self._video_title_var = StringVar(value="")
        self._video_title_label = ttk.Label(
            self, textvariable=self._video_title_var, font=("", 9, "italic")
        )
        self._video_title_label.grid(
            row=4, column=0, columnspan=3, padx=10, sticky="w"
        )

        # --- Per-video progress bar ---
        self._progress = ttk.Progressbar(
            self, mode="determinate", length=600
        )
        self._progress.grid(row=5, column=0, columnspan=3, padx=10, pady=(4, 2), sticky="ew")

        # --- Log output area ---
        self.log_text = scrolledtext.ScrolledText(
            self, wrap="word", state="disabled", height=18,
            font=("Consolas", 9)
        )
        self.log_text.grid(
            row=6, column=0, columnspan=3, padx=10, pady=(4, 10), sticky="nsew"
        )

        # Column weights for resize
        self.columnconfigure(1, weight=1)
        self.rowconfigure(6, weight=1)

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------

    def _load_config(self):
        """Load settings from the shared ``config.json`` at project root."""
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self._url_var.set(cfg.get("YOUTUBE_PLAYLIST", ""))
            self._dir_var.set(cfg.get("DOWNLOAD_DIR", ""))
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Use defaults (empty fields).

    def _save_config(self):
        """Save current settings to the shared ``config.json`` at project root."""
        cfg = {
            "YOUTUBE_PLAYLIST": self._url_var.get().strip(),
            "DOWNLOAD_DIR": self._dir_var.get().strip(),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _browse_directory(self):
        """Open a directory picker dialog."""
        chosen = filedialog.askdirectory(
            title="Select download directory",
            initialdir=self._dir_var.get() or os.path.expanduser("~"),
        )
        if chosen:
            self._dir_var.set(chosen)

    def _toggle_download(self):
        """Start or cancel the download based on the current button text."""
        if self._action_btn.cget("text") == "Cancel":
            self._cancel_download()
        else:
            self._start_download()

    def _start_download(self):
        """Validate inputs, start the worker thread, begin polling."""
        url = self._url_var.get().strip()
        directory = self._dir_var.get().strip()

        if not url:
            messagebox.showerror("Missing field", "Please enter a playlist URL.")
            return
        if not directory:
            messagebox.showerror("Missing field", "Please select a download directory.")
            return
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError as exc:
                messagebox.showerror(
                    "Invalid directory",
                    f"Cannot create directory:\n{directory}\n\n{exc}",
                )
                return

        # Persist the current configuration.
        self._save_config()

        # Lock the UI.
        self._url_entry.configure(state="disabled")
        self._dir_entry.configure(state="disabled")
        self._browse_btn.configure(state="disabled")
        self._action_btn.configure(text="Cancel")

        # Reset progress.
        self._video_label.configure(text="Video: -- of --")
        self._video_title_var.set("")
        self._progress.configure(value=0, maximum=100)
        self._clear_log()

        # Build the worker.
        self._cancel_event = threading.Event()
        self._queue = Queue()
        self._worker = DownloadWorker(
            download_dir=directory,
            playlist_url=url,
            queue=self._queue,
            cancel_event=self._cancel_event,
        )
        self._worker.start()
        self._polling = True
        self._poll_queue()

    def _cancel_download(self):
        """Signal the worker to stop after the current video."""
        if self._cancel_event:
            self._cancel_event.set()
        self._action_btn.configure(text="Stopping…", state="disabled")

    def _poll_queue(self):
        """Drain the queue periodically (called via ``tk.after``)."""
        if self._queue is None:
            return
        try:
            while True:
                msg_type, payload = self._queue.get_nowait()

                if msg_type == "log":
                    self._append_log(payload)
                elif msg_type == "progress":
                    n, total = payload
                    if total > 0:
                        self._progress.configure(maximum=total, value=n)
                elif msg_type == "done":
                    self._progress.configure(value=self._progress.cget("maximum"))
                    self._on_download_done()
                elif msg_type == "error":
                    self._append_log(f"ERROR: {payload}")
                    self._on_download_done()

        except Empty:
            pass

        if self._polling:
            self.after(100, self._poll_queue)

    def _on_download_done(self):
        """Re-enable the UI after download completes or is cancelled."""
        self._polling = False
        self._url_entry.configure(state="normal")
        self._dir_entry.configure(state="normal")
        self._browse_btn.configure(state="normal")
        self._action_btn.configure(text="Start Download", state="normal")
        self._worker = None

    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------

    def _append_log(self, text: str):
        """Append *text* to the log widget, capping at 1000 lines.

        Filter out yt-dlp ``[download]`` chunk lines since the progress
        bar already shows that information.
        """
        # Skip raw yt-dlp download progress — the progress bar handles it.
        if text.startswith("[download]"):
            return

        self._parse_video_counter(text)

        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")

        # Cap at 1000 lines to prevent UI lag.
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > 1000:
            self.log_text.delete("1.0", f"{line_count - 1000}.0")

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        """Remove all content from the log widget."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _parse_video_counter(self, text: str):
        """Look for ``Processing video X of Y`` in *text* and update labels."""
        import re  # noqa: re imported here to keep top-level minimal

        m = re.search(r"Processing video (\d+) of (\d+)", text)
        if m:
            idx, total = m.group(1), m.group(2)
            self._video_label.configure(text=f"Video: {idx} of {total}")

        # If the text looks like a video URL/ID, show it as the current title.
        # The log line has the format: "Processing video X of Y <webpage_url>"
        # We extract the last word as the URL.
        parts = text.split()
        for part in parts:
            if part.startswith("http"):
                self._video_title_var.set(part)
                break

    # ------------------------------------------------------------------
    # Window close
    # ------------------------------------------------------------------

    def _on_closing(self):
        """Save config and clean up before exiting."""
        self._save_config()
        if self._cancel_event and not self._cancel_event.is_set():
            self._cancel_event.set()
        self.destroy()


def main():
    """Launch the GUI application."""
    app = PlaylistDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
