"""Define the different ways to expose the program functionality.

Functions:
    load_logger: Configure the Logging logger.
"""

import logging
import sys
from enum import Enum


class ANSIFGColorCode(Enum):
    """ANSI escape codes for colored output."""

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    RESET = 0


class ConsoleColorFormatter(logging.Formatter):
    """Custom formatter that prints log levels to the console as colored plus signs."""

    # ANSI escape codes for colored output
    colors = {
        logging.DEBUG: ANSIFGColorCode.WHITE,
        # There are only 2 named levels under WARNING, we need 3 levels of verbosity
        # Using half-way between DEBUG and INFO as additional verbosity level
        # It is currently used for logging unchanged files
        15: ANSIFGColorCode.GREEN,
        logging.INFO: ANSIFGColorCode.CYAN,
        logging.WARNING: ANSIFGColorCode.YELLOW,
        logging.ERROR: ANSIFGColorCode.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log records as a colored plus sign followed by the log message."""
        color = self.colors.get(record.levelno, ANSIFGColorCode.RESET)
        self._style._fmt = f"[\033[{color.value}m+\033[0m] %(message)s"  # noqa: W0212
        return super().format(record)


def load_logger(verbose: int = 0) -> None:
    """Configure the Logging logger.

    Args:
        verbose: Allow more detailed logging output.
    """
    log_level = logging.INFO - verbose * 5
    logging.basicConfig(stream=sys.stderr, level=log_level)
    for handler in logging.getLogger().handlers:
        handler.setFormatter(ConsoleColorFormatter())
