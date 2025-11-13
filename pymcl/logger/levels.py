from enum import Enum

class LogLevel(Enum):
    # log severity levels
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

    def __lt__(self, other):
        if isinstance(other, LogLevel):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, LogLevel):
            return self.value <= other.value
        return NotImplemented

