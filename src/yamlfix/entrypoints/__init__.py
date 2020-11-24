"""Define the different ways to expose the program functionality.

Functions:
    load_logger: Configure the Logging logger.
"""

import logging
import sys

log = logging.getLogger(__name__)


def load_logger(verbose: bool = False) -> None:
    """Configure the Logging logger.

    Args:
        verbose: Set the logging level to Debug.
    """
    logging.addLevelName(logging.INFO, "[\033[36m+\033[0m]")
    logging.addLevelName(logging.ERROR, "[\033[31m+\033[0m]")
    logging.addLevelName(logging.DEBUG, "[\033[32m+\033[0m]")
    logging.addLevelName(logging.WARNING, "[\033[33m+\033[0m]")
    if verbose:
        logging.basicConfig(
            stream=sys.stderr, level=logging.DEBUG, format="  %(levelname)s %(message)s"
        )
    else:
        logging.basicConfig(
            stream=sys.stderr, level=logging.INFO, format="  %(levelname)s %(message)s"
        )
