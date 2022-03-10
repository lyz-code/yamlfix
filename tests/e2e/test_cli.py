"""Test the command line interface."""

import logging
import re
from textwrap import dedent

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from py._path.local import LocalPath

from yamlfix.entrypoints.cli import cli
from yamlfix.version import __version__


@pytest.fixture(name="runner")
def fixture_runner() -> CliRunner:
    """Configure the Click cli test runner."""
    return CliRunner(mix_stderr=False)


def test_version(runner: CliRunner) -> None:
    """Prints program version when called with --version."""
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert re.match(
        rf" *yamlfix version: {__version__}\n" r" *python version: .*\n *platform: .*",
        result.stdout,
    )


def test_corrects_one_file(runner: CliRunner, tmpdir: LocalPath) -> None:
    """Correct the source code of a file."""
    # ignore: call to untyped join method, they don't have type hints
    test_file = tmpdir.join("source.yaml")  # type: ignore
    test_file.write("program: yamlfix")
    fixed_source = dedent(
        """\
        ---
        program: yamlfix
        """
    )

    result = runner.invoke(cli, [str(test_file)])

    assert result.exit_code == 0
    assert test_file.read() == fixed_source


@pytest.mark.secondary()
def test_corrects_three_files(runner: CliRunner, tmpdir: LocalPath) -> None:
    """Correct the source code of multiple files."""
    test_files = []
    for file_number in range(3):
        # ignore: call to untyped join method, they don't have type hints
        test_file = tmpdir.join(f"source_{file_number}.yaml")  # type: ignore
        test_file.write("program: yamlfix")
        test_files.append(test_file)
    fixed_source = dedent(
        """\
        ---
        program: yamlfix
        """
    )

    result = runner.invoke(cli, [str(test_file) for test_file in test_files])

    assert result.exit_code == 0
    for test_file in test_files:
        assert test_file.read() == fixed_source


def test_corrects_code_from_stdin(runner: CliRunner) -> None:
    """Correct the source code passed as stdin."""
    source = "program: yamlfix"
    fixed_source = dedent(
        """\
        ---
        program: yamlfix
        """
    )

    result = runner.invoke(cli, ["-"], input=source)

    assert result.exit_code == 0
    assert result.stdout == fixed_source


@pytest.mark.secondary()
@pytest.mark.parametrize("verbose", [True, False])
def test_verbose_option(runner: CliRunner, verbose: bool) -> None:
    """Prints debug level logs only when called with --verbose"""
    # Clear logging handlers for logs to work with CliRunner
    # For more info see https://github.com/pallets/click/issues/1053)
    logging.getLogger().handlers = []
    source = "program: yamlfix"
    args = ["-", "--verbose"] if verbose else ["-"]

    result = runner.invoke(cli, args, input=source)

    debug_log_format = "[\033[32m+\033[0m]"
    if verbose:
        assert debug_log_format in result.stderr
    else:
        assert debug_log_format not in result.stderr


def test_ignores_correct_files(
    runner: CliRunner, tmpdir: LocalPath, caplog: LogCaptureFixture
) -> None:
    """Correct the source code of an already correct file."""
    # ignore: call to untyped join method, they don't have type hints
    caplog.set_level(logging.DEBUG)
    test_file = tmpdir.join("source.yaml")  # type: ignore
    test_file.write("---\na: 1\n")

    result = runner.invoke(cli, [str(test_file)])

    assert result.exit_code == 0
    assert test_file.read() == "---\na: 1\n"
    assert (
        "yamlfix.services",
        logging.DEBUG,
        f"Left file {test_file} unmodified.",
    ) in caplog.record_tuples
