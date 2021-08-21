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


def test_fix_code_preserves_indented_comments() -> None:
    """Don't remove indentation from comments in the code."""
    source = dedent(
        """\
        ---
        - program:
          # Keep comments!"""
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


def test_fix_code_adds_space_in_comment() -> None:
    """Correct comments that don't have a space between
    the # and the first character.
    """
    source = dedent(
        """\
        ---
        #This is a comment
        project: yamlfix"""
    )
    fixed_source = dedent(
        """\
        ---
        # This is a comment
        project: yamlfix"""
    )

    result = fix_code(source)

    assert result == fixed_source


def test_fix_code_not_add_extra_space_in_comment() -> None:
    """Respects comments that already have a space between
    the # and the first character.
    """
    source = dedent(
        """\
        ---
        # This is a comment
        project: yamlfix"""
    )
    fixed_source = dedent(
        """\
        ---
        # This is a comment
        project: yamlfix"""
    )

    result = fix_code(source)

    assert result == fixed_source


def test_fix_code_add_space_inline_comment() -> None:
    """Fix inline comments that don't have a space between
    the # and the first character.
    """
    source = dedent(
        """\
        ---
        project: yamlfix  #This is a comment"""
    )
    fixed_source = dedent(
        """\
        ---
        project: yamlfix  # This is a comment"""
    )

    result = fix_code(source)

    assert result == fixed_source


def test_fix_code_respects_url_anchors() -> None:
    """Comments that contain a url with an anchor should be respected."""
    source = dedent(
        """\
        ---
        # https://lyz-code.github.io/yamlfix/#usage
        foo: bar"""
    )

    result = fix_code(source)

    assert result == source


def test_fix_code_add_extra_space_inline_comment() -> None:
    """Fix inline comments that don't have two spaces before
    the #.
    """
    source = dedent(
        """\
        ---
        project: yamlfix # This is a comment"""
    )
    fixed_source = dedent(
        """\
        ---
        project: yamlfix  # This is a comment"""
    )

    result = fix_code(source)

    assert result == fixed_source


def test_fix_code_doesnt_change_double_exclamation_marks() -> None:
    """Lines with starting double exclamation marks should be respected, otherwise
    some programs like mkdocs-mermaidjs fail.
    """
    source = dedent(
        """\
        ---
        format: !!python/name:mermaid2.fence_mermaid"""
    )

    result = fix_code(source)

    assert result == source


def test_fix_code_parses_files_with_multiple_documents() -> None:
    """Files that contain multiple documents should be parsed as a collection of
    separate documents and then dumped together again.
    """
    source = dedent(
        """\
        ---
        project: yamlfix
        ---
        project: yamlfix"""
    )

    result = fix_code(source)

    assert result == source
