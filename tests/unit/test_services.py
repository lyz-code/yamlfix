"""Tests the service layer."""

from textwrap import dedent

import pytest

from yamlfix.services import fix_code

true_strings = [
    "TRUE",
    "True",
    "true",
    "YES",
    "Yes",
    "yes",
    "ON",
    "On",
    "on",
]

false_strings = [
    "FALSE",
    "False",
    "false",
    "NO",
    "No",
    "no",
    "OFF",
    "Off",
    "off",
]


def test_fix_code_adds_header() -> None:
    """Adds the --- at the beginning of the source."""
    source = "program: yamlfix"
    fixed_source = dedent(
        """\
        ---
        program: yamlfix"""
    )

    result = fix_code(source)

    assert result == fixed_source


def test_fix_code_doesnt_double_the_header() -> None:
    """If source starts with --- don't add another line."""
    source = dedent(
        """\
        ---
        program: yamlfix"""
    )

    result = fix_code(source)

    assert result == source


def test_fix_code_corrects_indentation_on_lists() -> None:
    """Use two spaces for indentation of lists."""
    source = dedent(
        """\
        ---
        hosts:
        - item1
        - item2"""
    )
    fixed_source = dedent(
        """\
        ---
        hosts:
          - item1
          - item2"""
    )

    result = fix_code(source)

    assert result == fixed_source


def test_fix_code_respects_parent_lists() -> None:
    """Do not indent lists at the first level."""
    source = dedent(
        """\
        ---
        - item1
        - item2"""
    )

    result = fix_code(source)

    assert result == source


def test_fix_code_preserves_comments() -> None:
    """Don't delete comments in the code."""
    source = dedent(
        """\
        ---
        # Keep comments!
        program: yamlfix"""
    )

    result = fix_code(source)

    assert result == source


def test_fix_code_respects_parent_lists_with_comments() -> None:
    """Do not indent lists at the first level even if there is a comment."""
    source = dedent(
        """\
        ---
        # Comment
        - item1
        - item2"""
    )

    result = fix_code(source)

    assert result == source


def test_fix_code_removes_extra_apostrophes() -> None:
    """Remove not needed apostrophes."""
    source = dedent(
        """\
        ---
        title: 'Why we sleep'"""
    )
    fixed_source = dedent(
        """\
        ---
        title: Why we sleep"""
    )

    result = fix_code(source)

    assert result == fixed_source


@pytest.mark.parametrize("true_string", true_strings)
def test_fix_code_converts_non_valid_true_booleans(true_string: str) -> None:
    """Convert common strings that refer to true, but aren't the string `true`.

    [More
    info](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy)
    """
    source = dedent(
        f"""\
        ---
        True dictionary: {true_string}
        True list:
          - {true_string}"""
    )
    fixed_source = dedent(
        """\
        ---
        True dictionary: true
        True list:
          - true"""
    )

    result = fix_code(source)

    assert result == fixed_source


@pytest.mark.parametrize("false_string", false_strings)
def test_fix_code_converts_non_valid_false_booleans(false_string: str) -> None:
    """Convert common strings that refer to false, but aren't the string `false`.

    [More
    info](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy)
    """
    source = dedent(
        f"""\
        ---
        False dictionary: {false_string}
        False list:
          - {false_string}"""
    )
    fixed_source = dedent(
        """\
        ---
        False dictionary: false
        False list:
          - false"""
    )

    result = fix_code(source)

    assert result == fixed_source


@pytest.mark.parametrize("truthy_string", true_strings + false_strings)
def test_fix_code_respects_apostrophes_for_truthy_substitutions(
    truthy_string: str,
) -> None:
    """Keep apostrophes for strings like `yes` or `true`.

    So they are not converted to booleans.
    """
    source = dedent(
        f"""\
        ---
        title: '{truthy_string}'"""
    )

    result = fix_code(source)

    assert result == source
