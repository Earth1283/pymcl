import threading
from datetime import datetime
from .levels import LogLevel


class Formatter:
    """Formats log messages with consistent structure."""

    def __init__(self, fmt=None):
        """
        Initialize formatter.

        Args:
            fmt: Custom format string. Available keys:
                 {timestamp}, {level}, {logger}, {thread}, {message}
        """
        self.fmt = fmt or "[{timestamp}] [{level:8}] [{logger}] [{thread}] {message}"

    def format(self, logger_name, level, message):
        """
        Format a log message.

        Args:
            logger_name: Name of the logger
            level: LogLevel enum value
            message: The log message

        Returns:
            Formatted string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        thread_name = threading.current_thread().name

        return self.fmt.format(
            timestamp=timestamp,
            level=level.name,
            logger=logger_name,
            thread=thread_name,
            message=message
        )
