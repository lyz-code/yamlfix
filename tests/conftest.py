"""Store the classes and fixtures used throughout the tests."""

import os

import pytest


@pytest.fixture(autouse=True)
def _unset_yamlfix_config_path() -> None:
    """Unset YAMLFIX_CONFIG_PATH environment variable."""
    os.environ.pop("YAMLFIX_CONFIG_PATH", None)
