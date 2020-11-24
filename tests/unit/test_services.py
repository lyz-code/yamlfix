"""Tests the service layer."""

from textwrap import dedent

from yamlfix.services import fix_code


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
    """Use two spaces for indentation."""
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
