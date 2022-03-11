"""Utilities to retrieve the information of the program version."""

import platform
import sys

# Do not edit this line manually, let `make bump` do it.
__version__ = "0.9.0"


def version_info() -> str:
    """Display the version of the program, python and the platform."""
    info = {
        "yamlfix version": __version__,
        "python version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
    }
    return "\n".join(f"{k + ':' :>30} {v}" for k, v in info.items())
