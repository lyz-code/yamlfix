"""Define the different ways to expose the program functionality.

Functions:
    load_logger: Configure the Logging logger.
"""

import logging
import sys


class ConsoleColorFormatter(logging.Formatter):
    """Custom formatter that prints log levels to the console as colored plus signs."""

    # ANSI escape codes for colored output
    colors = {
        logging.DEBUG: 32,  # GREEN
        15: 34,  # BLUE
        logging.INFO: 36,  # CYAN
        logging.WARNING: 33,  # YELLOW
        logging.ERROR: 31,  # RED
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log records as a colored plus sign followed by the log message."""
        color = self.colors.get(record.levelno, 0)
        self._style._fmt = f"[\033[{color}m+\033[0m] %(message)s"  # noqa: W0212
        return super().format(record)


def load_logger(verbose: int = 0) -> None:
    """Configure the Logging logger.

    Args:
        verbose: Decrease logging threshold by 10 for each level.
    """
    log_level = logging.INFO - verbose * 5
    logging.basicConfig(stream=sys.stderr, level=log_level)
    for handler in logging.getLogger().handlers:
        handler.setFormatter(ConsoleColorFormatter())
