"""Test the command line interface."""

import logging
import os
import re
from itertools import product
from pathlib import Path
from textwrap import dedent

import py  # type: ignore
import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

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
    assert re.search(
        rf" *yamlfix: {__version__}\n *Python: .*\n *Platform: .*", result.stdout
    )


def test_corrects_one_file(runner: CliRunner, tmp_path: Path) -> None:
    """Correct the source code of a file."""
    test_file = tmp_path / "source.yaml"
    test_file.write_text("program: yamlfix")
    fixed_source = dedent(
        """\
        ---
        program: yamlfix
        """
    )

    result = runner.invoke(cli, [str(test_file)])

    assert result.exit_code == 0
    assert test_file.read_text() == fixed_source


@pytest.mark.secondary()
def test_corrects_three_files(runner: CliRunner, tmp_path: Path) -> None:
    """Correct the source code of multiple files."""
    test_files = []
    for file_number in range(3):
        test_file = tmp_path / f"source_{file_number}.yaml"
        test_file.write_text("program: yamlfix")
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
        assert test_file.read_text() == fixed_source


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


def test_include_exclude_files(runner: CliRunner, tmp_path: Path) -> None:
    """Correct only files matching include, and ignore files matching exclude."""
    include1 = tmp_path / "source_1.yaml"
    exclude1 = tmp_path / "source_2.txt"
    (tmp_path / "foo").mkdir()
    exclude2 = tmp_path / "foo" / "source_3.yaml"
    (tmp_path / "foo" / "bar").mkdir()
    exclude3 = tmp_path / "foo" / "bar" / "source_4.yaml"
    (tmp_path / "foo" / "baz").mkdir()
    exclude4 = tmp_path / "foo" / "baz" / "source_5.yaml"
    test_files = [include1, exclude1, exclude2, exclude3, exclude4]
    init_source = "program: yamlfix"
    for test_file in test_files:
        test_file.write_text(init_source)
    fixed_source = dedent(
        """\
        ---
        program: yamlfix
        """
    )

    result = runner.invoke(
        cli,
        [str(tmp_path)]
        + [
            "--include",
            "*.yaml",
            "--exclude",
            "foo/*.yaml",
            "--exclude",
            "foo/**/*.yaml",
        ],
    )

    assert result.exit_code == 0
    assert include1.read_text() == fixed_source
    assert exclude1.read_text() == init_source
    assert exclude2.read_text() == init_source
    assert exclude3.read_text() == init_source
    assert exclude4.read_text() == init_source


@pytest.mark.secondary()
@pytest.mark.parametrize(
    ("verbose", "requires_fixing"), product([0, 1, 2], [True, False])
)
def test_verbose_option(runner: CliRunner, verbose: int, requires_fixing: bool) -> None:
    """Prints debug level logs only when called with --verbose"""
    # Clear logging handlers for logs to work with CliRunner
    # For more info see https://github.com/pallets/click/issues/1053)
    logging.getLogger().handlers = []
    source = "program: yamlfix" if requires_fixing else "---\nprogram: yamlfix\n"
    args = ["-"]
    if verbose >= 1:
        args.append("--verbose")
    if verbose >= 2:
        args.append("-v")

    result = runner.invoke(cli, args, input=source)

    debug_log_format = "[\033[37m+\033[0m]"
    unchanged_log_format = "[\033[32m+\033[0m]"
    info_log_format = "[\033[36m+\033[0m]"
    # Check that changes are printed at info level
    assert (f"{info_log_format} Fixed <stdin>" in result.stderr) == requires_fixing
    if verbose == 0:
        assert debug_log_format not in result.stderr
        assert unchanged_log_format not in result.stderr
    if verbose >= 1:
        # If no changes are required, unchanged log should not be printed
        assert (unchanged_log_format in result.stderr) != requires_fixing
    if verbose >= 2:
        assert debug_log_format in result.stderr


def test_ignores_correct_files(
    runner: CliRunner, tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """Correct the source code of an already correct file."""
    # ignore: call to untyped join method, they don't have type hints
    caplog.set_level(logging.DEBUG)
    test_file = tmp_path / "source.yaml"
    test_file.write_text("---\na: 1\n")

    result = runner.invoke(cli, [str(test_file)])

    assert result.exit_code == 0
    assert test_file.read_text() == "---\na: 1\n"
    assert (
        "yamlfix.services",
        15,
        f"{test_file} is already well formatted",
    ) in caplog.record_tuples


def test_check_one_file_changes(runner: CliRunner, tmp_path: Path) -> None:
    """The --check flag is working with fixes to do."""
    # ignore: call to untyped join method, they don't have type hints
    test_file_source = "program: yamlfix"
    test_file = tmp_path / "source.yaml"
    test_file.write_text(test_file_source)

    result = runner.invoke(cli, [str(test_file), "--check"])

    assert result.exit_code == 1
    assert test_file.read_text() == test_file_source


def test_check_one_file_no_changes(runner: CliRunner, tmp_path: Path) -> None:
    """The --check flag is working with pending changes."""
    # ignore: call to untyped join method, they don't have type hints
    test_file_source = dedent(
        """\
        ---
        program: yamlfix
        """
    )
    test_file = tmp_path / "source.yaml"
    test_file.write_text(test_file_source)

    result = runner.invoke(cli, [str(test_file), "--check"])

    assert result.exit_code == 0
    assert test_file.read_text() == test_file_source


def test_config_parsing(runner: CliRunner, tmp_path: Path) -> None:
    """Provided config options are parsed, merged, and applied correctly."""
    os.environ["YAMLFIX_CONFIG_PATH"] = str(tmp_path)
    pyproject_config = dedent(
        """\
        [tool.yamlfix]
        line_length = 90
        quote_basic_values = "true"
        """
    )
    pyproject_config_file = tmp_path / "pyproject.toml"
    pyproject_config_file.write_text(pyproject_config)
    toml_config = dedent(
        """\
        none_representation = "null"
        quote_representation = '"'
        """
    )
    toml_config_file = tmp_path / "yamlfix.toml"
    toml_config_file.write_text(toml_config)

    # the ini config is currenlty parsed incorrectly and it is not possible to provide
    # a top level config option with it: https://github.com/dbatten5/maison/issues/199
    ini_config = dedent(
        """\
        [DEFAULT]
        quote_representation = "'"

        [yamlfix]
        none_representation = "~"
        """
    )
    ini_config_file = tmp_path / "yamlfix.ini"
    ini_config_file.write_text(ini_config)
    test_source = dedent(
        f"""\
        ---
        really_long_string: >
          {("abcdefghij " * 10).strip()}
        single_quoted_string: 'value1'
        double_quoted_string: "value2"
        unquoted_string: value3
        none_value:
        none_value2: ~
        none_value3: null
        none_value4: NULL
        """
    )
    test_source_file = tmp_path / "source.yaml"
    test_source_file.write_text(test_source)

    # we have to provide the pyproject.toml as a relative path to YAMLFIX_CONFIG_PATH
    # until this is fixed: https://github.com/dbatten5/maison/issues/141
    pyproject_config_file_name = "pyproject.toml"

    result = runner.invoke(
        cli,
        [
            "--config-file",
            pyproject_config_file_name,
            "--config-file",
            str(toml_config_file),
            "-c",
            str(ini_config_file),
            str(test_source_file),
        ],
    )

    assert result.exit_code == 0
    assert test_source_file.read_text() == dedent(
        f"""\
        ---
        really_long_string: >
          {("abcdefghij " * 9).strip()}
          abcdefghij
        single_quoted_string: "value1"
        double_quoted_string: "value2"
        unquoted_string: "value3"
        none_value: null
        none_value2: null
        none_value3: null
        none_value4: null
        """
    )


def test_read_prefixed_environment_variables(runner: CliRunner, tmp_path: Path) -> None:
    """Make sure environment variables are parsed into the config object"""
    os.environ["YAMLFIX_TEST_NONE_REPRESENTATION"] = "~"
    test_source = dedent(
        """\
        none_value:
        none_value2: ~
        none_value3: null
        none_value4: NULL
        """
    )
    test_source_file = tmp_path / "source.yaml"
    test_source_file.write_text(test_source)

    result = runner.invoke(cli, ["--env-prefix", "YAMLFIX_TEST", str(test_source_file)])

    assert result.exit_code == 0
    assert test_source_file.read_text() == dedent(
        """\
        ---
        none_value: ~
        none_value2: ~
        none_value3: ~
        none_value4: ~
        """
    )


def test_sequence_style_env_enum_parsing(runner: CliRunner, tmp_path: Path) -> None:
    """Make sure that the enum-value can be parsed from string through an env var."""
    os.environ["YAMLFIX_SEQUENCE_STYLE"] = "block_style"
    os.environ["YAMLFIX_QUOTE_BASIC_VALUES"] = "false"
    test_source = dedent(
        """\
        list1: [item, item]
        list2:
          - item
          - item
        """
    )
    test_source_file = tmp_path / "source.yaml"
    test_source_file.write_text(test_source)

    result = runner.invoke(cli, [str(test_source_file)])

    assert result.exit_code == 0
    assert test_source_file.read_text() == dedent(
        """\
        ---
        list1:
          - item
          - item
        list2:
          - item
          - item
        """
    )


def test_find_files(runner: CliRunner, tmp_path: Path) -> None:
    """Correct the source code of multiple files."""
    test_files = []
    (tmp_path / ".hidden").mkdir()
    for filename in [
        "test.yaml",
        "test.yml",
        ".test.yaml",
        ".test.yml",
        ".hidden/test.yaml",
    ]:
        file_path = tmp_path / filename
        file_path.write_text("program: yamlfix")
        test_files.append(file_path)
    fixed_source = dedent(
        """\
        ---
        program: yamlfix
        """
    )

    result = runner.invoke(cli, [str(tmp_path)])

    assert result.exit_code == 0
    for test_file in test_files:
        assert test_file.read_text() == fixed_source


def test_no_yaml_files(
    runner: CliRunner, tmp_path: Path, caplog: LogCaptureFixture
) -> None:
    """Correct the source code of multiple files."""
    result = runner.invoke(cli, [str(tmp_path)])

    assert result.exit_code == 0
    assert (
        "yamlfix.entrypoints.cli",
        logging.WARNING,
        "No YAML files found!",
    ) == caplog.record_tuples[0]


def test_std_and_file_error(runner: CliRunner, tmp_path: Path) -> None:
    """Correct the source code of multiple files."""
    filepath = tmp_path / "test.yaml"
    filepath.write_text("program: yamlfix")

    result = runner.invoke(cli, ["-", str(filepath)])

    assert result.exit_code == 1
    assert (
        str(result.exception) == "Cannot specify '-' and other files at the same time."
    )


def test_do_not_read_folders_as_files(runner: CliRunner, tmpdir: py.path.local) -> None:
    """Skips folders that have a .yml or .yaml extension."""
    tmpdir.mkdir("folder.yml")

    result = runner.invoke(cli, [str(tmpdir)])

    assert result.exit_code == 0
