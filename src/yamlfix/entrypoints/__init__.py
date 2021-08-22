"""Define the different ways to expose the program functionality.

Functions:
    load_logger: Configure the Logging logger.
"""

import logging
import sys

# Ansi color codes
RED = 31
YELLOW = 33
CYAN = 36
GREEN = 32


class ConsoleColorFormatter(logging.Formatter):
    """Custom formatter that prints log levels to the console as colored plus signs."""

    colors = {
        logging.DEBUG: GREEN,
        logging.INFO: CYAN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log records as a colored plus sign followed by the log message."""
        color = self.colors.get(record.levelno, 0)
        self._style._fmt = f"[\033[{color}m+\033[0m] %(message)s"
        return super().format(record)


def load_logger(verbose: bool = False) -> None:
    """Configure the Logging logger.

    Args:
        verbose: Set the logging level to Debug.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(stream=sys.stderr, level=log_level)
    for handler in logging.getLogger().handlers:
        handler.setFormatter(ConsoleColorFormatter())
