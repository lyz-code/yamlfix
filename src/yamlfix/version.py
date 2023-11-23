"""Utilities to retrieve the information of the program version."""

import platform
import sys
from textwrap import dedent

# Do not edit this line manually, let `make bump` do it.
__version__ = "1.16.0"


def version_info() -> str:
    """Display the version of the program, python and the platform."""
    return dedent(
        f"""\
        ------------------------------------------------------------------
             yamlfix: {__version__}
             Python: {sys.version.split(" ", maxsplit=1)[0]}
             Platform: {platform.platform()}
        ------------------------------------------------------------------"""
    )
