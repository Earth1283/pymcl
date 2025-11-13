import sys
import threading
from pathlib import Path
from abc import ABC, abstractmethod


class Handler(ABC):
    """Base class for log handlers."""

    def __init__(self):
        self._lock = threading.Lock()

    @abstractmethod
    def emit(self, formatted_message):
        """
        Emit a formatted log message.

        Args:
            formatted_message: Pre-formatted log string
        """
        pass

    def write(self, formatted_message):
        """Thread-safe write wrapper."""
        with self._lock:
            self.emit(formatted_message)


class ConsoleHandler(Handler):
    """Handler that writes to console (stdout)."""

    def __init__(self, stream=None):
        """
        Initialize console handler.

        Args:
            stream: Output stream (default: sys.stdout)
        """
        super().__init__()
        self.stream = stream or sys.stdout

    def emit(self, formatted_message):
        """Write to console."""
        print(formatted_message, file=self.stream, flush=True)


class FileHandler(Handler):
    """Handler that writes to a file."""

    def __init__(self, filepath, mode='a', encoding='utf-8'):
        """
        Initialize file handler.

        Args:
            filepath: Path to log file
            mode: File open mode (default: 'a' for append)
            encoding: File encoding (default: 'utf-8')
        """
        super().__init__()
        self.filepath = Path(filepath)
        self.mode = mode
        self.encoding = encoding

        # Create parent directories if needed
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, formatted_message):
        """Write to file."""
        try:
            with open(self.filepath, self.mode, encoding=self.encoding) as f:
                f.write(formatted_message + '\n')
        except Exception as e:
            print(f"ERROR: Failed to write to log file: {e}", file=sys.stderr)
