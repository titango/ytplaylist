"""Tests for lib/file.py."""
from lib.file import (
    sanitize_filename,
    check_duplicate_name,
    log_message,
)


class TestSanitizeFilename:
    """sanitize_filename replaces path-unsafe chars with '-', leaves others alone."""

    def test_normal_filename_passes_through(self):
        """Should leave plain filenames unchanged."""
        assert sanitize_filename("Hello World") == "Hello World"
        assert sanitize_filename("song_123.mp3") == "song_123.mp3"

    def test_replaces_forward_slash(self):
        """Forward slash becomes hyphen."""
        assert sanitize_filename("a/b/c") == "a-b-c"

    def test_replaces_backslash(self):
        """Backslash becomes hyphen."""
        assert sanitize_filename("a\\b\\c") == "a-b-c"

    def test_replaces_colon(self):
        """Colon becomes hyphen."""
        assert sanitize_filename("a:b") == "a-b"

    def test_replaces_asterisk(self):
        """Asterisk becomes hyphen."""
        assert sanitize_filename("a*b") == "a-b"

    def test_replaces_question_mark(self):
        """Question mark becomes hyphen."""
        assert sanitize_filename("a?b") == "a-b"

    def test_replaces_quotes(self):
        """Double quote becomes hyphen."""
        assert sanitize_filename('a"b') == "a-b"

    def test_replaces_angle_brackets(self):
        """Angle brackets become hyphens."""
        assert sanitize_filename("a<b>c") == "a-b-c"

    def test_replaces_pipe(self):
        """Pipe character becomes hyphen."""
        assert sanitize_filename("a|b") == "a-b"

    def test_handles_empty_string(self):
        """Empty string should return empty string."""
        assert sanitize_filename("") == ""

    def test_handles_multiple_special_chars(self):
        """Multiple consecutive special chars each become a hyphen."""
        # Each of / : * ? " becomes a -, so ?" becomes --
        assert sanitize_filename('a/b:c*d?"e"') == "a-b-c-d--e-"


class TestCheckDuplicateName:
    """check_duplicate_name returns True if the file exists, False otherwise."""

    def test_returns_true_when_file_exists(self, tmp_path):
        """Should return True when a file with that name exists in the directory."""
        song = tmp_path / "song.mp3"
        song.write_text("data")
        assert check_duplicate_name("song.mp3", str(tmp_path)) is True

    def test_returns_false_when_file_does_not_exist(self, tmp_path):
        """Should return False when the file does not exist."""
        assert check_duplicate_name("nonexistent.mp3", str(tmp_path)) is False

    def test_strips_filename_whitespace(self, tmp_path):
        """Leading/trailing whitespace on filename should be stripped before checking."""
        song = tmp_path / "song.mp3"
        song.write_text("data")
        assert check_duplicate_name("  song.mp3  ", str(tmp_path)) is True


class TestLogMessage:
    """log_message prints to stdout and optionally writes to a log file."""

    def test_prints_to_stdout(self, capsys):
        """Should print the message followed by a newline to stdout."""
        log_message("hello world")
        captured = capsys.readouterr()
        assert captured.out == "hello world\n"

    def test_logs_multiple_messages(self, capsys):
        """Each call should print its own line."""
        log_message("first")
        log_message("second")
        captured = capsys.readouterr()
        assert captured.out == "first\nsecond\n"

    def test_writes_to_log_file_when_enabled(self, tmp_path, monkeypatch):
        """Should append to the log file when IS_LOGGING is True."""
        monkeypatch.setattr("lib.file.IS_LOGGING", True)
        log_path = tmp_path / "test_log.txt"
        monkeypatch.setattr("lib.file.LOG_FILE_PATH", str(log_path))

        log_message("log entry")

        assert log_path.read_text() == "log entry\n"

    def test_does_not_write_to_log_file_when_disabled(self, tmp_path, monkeypatch):
        """Should not create a log file when IS_LOGGING is False."""
        monkeypatch.setattr("lib.file.IS_LOGGING", False)
        log_path = tmp_path / "test_log.txt"
        monkeypatch.setattr("lib.file.LOG_FILE_PATH", str(log_path))

        log_message("should not appear")

        assert not log_path.exists()
