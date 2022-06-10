"""Test the version message"""

import platform
import sys

from yamlfix.version import __version__, version_info


def test_version() -> None:
    """
    Given: Nothing
    When: version_info is called
    Then: the expected output is given
    """
    result = version_info()

    assert sys.version.split(" ", maxsplit=1)[0] in result
    assert platform.platform() in result
    assert __version__ in result
