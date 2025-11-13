from .levels import LogLevel
from .formatter import Formatter
from .handlers import Handler, ConsoleHandler

class Logger:
     def __init__(self, name="app", min_level=LogLevel.INFO):
        """
        Initialize logger.

        Args:
            name: Logger name (appears in log messages)
            min_level: Minimum log level to display
        """
        self.name = name
        self.min_level = min_level
        self.formatter = Formatter()
        self.handlers = []

    def add_handler(self, handler):
        """
        Add a log handler.

        Args:
            handler: Handler instance (ConsoleHandler, FileHandler, etc.)
        """
        if isinstance(handler, Handler):
            self.handlers.append(handler)
        else:
            raise TypeError("Handler must be an instance of Handler class")

    def set_formatter(self, formatter):
        """
        Set custom formatter.

        Args:
            formatter: Formatter instance
        """
        self.formatter = formatter

    def set_level(self, level):
        """
        Set minimum log level.

        Args:
            level: LogLevel enum value
        """
        self.min_level = level

    def _log(self, level, message):
        """Internal logging method."""
        if level < self.min_level:
            return

        # Format message once
        formatted = self.formatter.format(self.name, level, message)

        # Write to all handlers
        for handler in self.handlers:
            handler.write(formatted)

    def debug(self, message):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message)

    def info(self, message):
        """Log info message."""
        self._log(LogLevel.INFO, message)

    def warning(self, message):
        """Log warning message."""
        self._log(LogLevel.WARNING, message)

    def error(self, message):
        """Log error message."""
        self._log(LogLevel.ERROR, message)

    def critical(self, message):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message)
