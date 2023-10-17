"""Tests the service layer."""

import logging
from pathlib import Path
from textwrap import dedent
from typing import Optional

import pytest

from yamlfix import fix_files
from yamlfix.model import YamlfixConfig, YamlNodeStyle
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


class TestFixFiles:
    """Test the fix_files function."""

    def test_fix_files_can_process_string_arguments(self, tmp_path: Path) -> None:
        """
        Given: A file to fix
        When: Passing the string with the path to the file to fix_files
        Then: The file is fixed
        """
        test_file = tmp_path / "source.yaml"
        test_file.write_text("program: yamlfix")
        fixed_source = dedent(
            """\
            ---
            program: yamlfix
            """
        )

        fix_files([str(test_file)], False)  # act

        assert test_file.read_text() == fixed_source

    def test_fix_files_issues_warning(self, tmp_path: Path) -> None:
        """
        Given: A file to fix
        When: Using the old signature
        Then: A warning is issued
        """
        test_file = tmp_path / "source.yaml"
        test_file.write_text("program: yamlfix")

        with pytest.warns(UserWarning, match="yamlfix/pull/182"):
            fix_files([str(test_file)])


class TestFixCode:
    """Test the fix_code function."""

    def test_fix_code_ignore_jinja2(self) -> None:
        """Ignores jinja2 line if present at the beginning of the source."""
        source = dedent(
            """\
            # jinja2:lstrip_blocks: true
            ---
            program: yamlfix
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_ignore_shebang(self) -> None:
        """Ignores shebang lines if present at the beginning of the source."""
        source = dedent(
            """\
            #! /this/line/should/be/ignored
            ---
            program: yamlfix
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_ignore_ansible_vaults(self) -> None:
        """Adds the --- at the beginning of the source."""
        source = dedent(
            """\
            $ANSIBLE_VAULT;1.1;AES256
            3036303361343731386530393763...
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_adds_header(self) -> None:
        """Adds the --- at the beginning of the source."""
        source = "program: yamlfix"
        fixed_source = dedent(
            """\
            ---
            program: yamlfix
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    def test_fix_code_doesnt_double_the_header(self) -> None:
        """If source starts with --- don't add another line."""
        source = dedent(
            """\
            ---
            program: yamlfix
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_corrects_indentation_on_lists(self) -> None:
        """Use two spaces for indentation of lists."""
        source = dedent(
            """\
            ---
            hosts:
            - item1
            - item2
            """
        )
        fixed_source = dedent(
            """\
            ---
            hosts:
              - item1
              - item2
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.KEEP_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_fix_code_respects_parent_lists(self) -> None:
        """Do not indent lists at the first level."""
        source = dedent(
            """\
            ---
            - item1
            - item2
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_preserves_comments(self) -> None:
        """Don't delete comments in the code."""
        source = dedent(
            """\
            ---
            # Keep comments!
            program: yamlfix
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_respects_parent_lists_with_comments(self) -> None:
        """Do not indent lists at the first level even if there is a comment."""
        source = dedent(
            """\
            ---
            # Comment
            - item1
            - item2
            """
        )

        result = fix_code(source)

        assert result == source

    @pytest.mark.parametrize(
        "code",
        [
            dedent(
                """\
                ---
                - program:
                  # Keep comments!
                """
            ),
            dedent(
                """\
                ---
                - name: Setup SONiC Build Servers
                  hosts: sonic_build_server
                  vars:
                    # Keep comments!
                    build_user: build
                """
            ),
            dedent(
                """\
                ---
                tasks:
                  - name: Make sure repository is cloned  # noqa latest[git]
            """
            ),
        ],
    )
    def test_fix_code_preserves_indented_comments(self, code: str) -> None:
        """Don't remove indentation from comments in the code."""
        result = fix_code(code)

        assert result == code

    def test_fix_code_removes_extra_apostrophes(self) -> None:
        """Remove not needed apostrophes."""
        source = dedent(
            """\
            ---
            title: 'Why we sleep'
            """
        )
        fixed_source = dedent(
            """\
            ---
            title: Why we sleep
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    @pytest.mark.parametrize("true_string", true_strings)
    def test_fix_code_converts_non_valid_true_booleans(self, true_string: str) -> None:
        """Convert common strings that refer to true, but aren't the string `true`.

        [More
        info](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy)
        """
        source = dedent(
            f"""\
            ---
            True dictionary: {true_string}
            True list:
            - {true_string}
            """
        )
        fixed_source = dedent(
            """\
            ---
            True dictionary: true
            True list: [true]
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    @pytest.mark.parametrize("false_string", false_strings)
    def test_fix_code_converts_non_valid_false_booleans(
        self, false_string: str
    ) -> None:
        """Convert common strings that refer to false, but aren't the string `false`.

        [More
        info](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy)
        """
        source = dedent(
            f"""\
            ---
            False dictionary: {false_string}
            False list:
            - {false_string}
            """
        )
        fixed_source = dedent(
            """\
            ---
            False dictionary: false
            False list: [false]
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    @pytest.mark.parametrize("truthy_string", true_strings + false_strings)
    def test_fix_code_respects_apostrophes_for_truthy_substitutions(
        self,
        truthy_string: str,
    ) -> None:
        """Keep apostrophes for strings like `yes` or `true`.

        So they are not converted to booleans.
        """
        source = dedent(
            f"""\
            ---
            title: '{truthy_string}'
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_adds_space_in_comment(self) -> None:
        """Correct comments that don't have a space between
        the # and the first character.
        """
        source = dedent(
            """\
            ---
            #This is a comment
            project: yamlfix
            """
        )
        fixed_source = dedent(
            """\
            ---
            # This is a comment
            project: yamlfix
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    def test_fix_code_not_add_extra_space_in_comment(self) -> None:
        """Respects comments that already have a space between
        the # and the first character.
        """
        source = dedent(
            """\
            ---
            # This is a comment
            project: yamlfix
            """
        )
        fixed_source = dedent(
            """\
            ---
            # This is a comment
            project: yamlfix
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    def test_fix_code_add_space_inline_comment(self) -> None:
        """Fix inline comments that don't have a space between
        the # and the first character.
        """
        source = dedent(
            """\
            ---
            project: yamlfix  #This is a comment
            """
        )
        fixed_source = dedent(
            """\
            ---
            project: yamlfix  # This is a comment
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    def test_fix_code_respects_url_anchors(self) -> None:
        """Comments that contain a url with an anchor should be respected."""
        source = dedent(
            """\
            ---
            # https://lyz-code.github.io/yamlfix/#usage
            foo: bar
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_add_extra_space_inline_comment(self) -> None:
        """Fix inline comments that don't have two spaces before
        the #.
        """
        source = dedent(
            """\
            ---
            project: yamlfix # This is a comment
            """
        )
        fixed_source = dedent(
            """\
            ---
            project: yamlfix  # This is a comment
            """
        )

        result = fix_code(source)

        assert result == fixed_source

    def test_fix_code_doesnt_change_double_exclamation_marks(self) -> None:
        """Lines with starting double exclamation marks should be respected, otherwise
        some programs like mkdocs-mermaidjs fail.
        """
        source = dedent(
            """\
            ---
            format: !!python/name:mermaid2.fence_mermaid
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_parses_files_with_multiple_documents(self) -> None:
        """Files that contain multiple documents should be parsed as a collection of
        separate documents and then dumped together again.
        """
        source = dedent(
            """\
            ---
            project: yamlfix
            ---
            project: yamlfix
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_functions_emit_debug_logs(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Each fixer function should emit a log at the debug level in each run."""
        caplog.set_level(logging.DEBUG)

        fix_code("")  # act

        expected_logs = {
            "Setting up ruamel yaml 'quote simple values' configuration...",
            "Setting up ruamel yaml 'sequence flow style' configuration...",
            "Running ruamel yaml base configuration...",
            "Running source code fixers...",
            "Fixing truthy strings...",
            "Fixing jinja2 variables...",
            "Running ruamel yaml fixer...",
            "Restoring truthy strings...",
            "Restoring jinja2 variables...",
            "Restoring double exclamations...",
            "Fixing comments...",
            "Fixing top level lists...",
            "Fixing flow-style lists...",
        }
        assert set(caplog.messages) == expected_logs
        for record in caplog.records:
            assert record.levelname == "DEBUG"

    @pytest.mark.parametrize("whitespace", ["", "\n", "\n\n"])
    def test_fixed_code_has_exactly_one_newline_at_end_of_file(
        self,
        whitespace: str,
    ) -> None:
        """Files should have exactly one newline at the end to comply with the POSIX
        standard.
        """
        source = dedent(
            """\
            ---
            program: yamlfix"""
        )
        source += whitespace
        fixed_code = dedent(
            """\
            ---
            program: yamlfix
            """
        )

        result = fix_code(source)

        assert result == fixed_code

    def test_anchors_and_aliases_with_duplicate_merge_keys(self) -> None:
        """All anchors and aliases should be preserved even with multiple merge keys
        and merge keys should be formatted as a list in a single line.
        """
        source = dedent(
            """\
            ---
            x-node-volumes: &node-volumes
              node3_data:
            x-vault-volumes: &vault-volumes
              vault_data:
            x-mongo-volumes: &mongo-volumes
              mongo_data:
            x-certmgr-volumes: &certmgr-volumes
              cert_data:
            volumes:
              <<: *node-volumes
              <<: *vault-volumes
              <<: *mongo-volumes
              <<: *certmgr-volumes
            """
        )
        desired_source = dedent(
            """\
            ---
            x-node-volumes: &node-volumes
              node3_data:
            x-vault-volumes: &vault-volumes
              vault_data:
            x-mongo-volumes: &mongo-volumes
              mongo_data:
            x-certmgr-volumes: &certmgr-volumes
              cert_data:
            volumes:
              <<:
                - *node-volumes
                - *vault-volumes
                - *mongo-volumes
                - *certmgr-volumes
            """
        )
        config = YamlfixConfig()
        config.allow_duplicate_keys = True

        result = fix_code(source, config)

        assert result == desired_source

    def test_fix_code_respects_comment_symbol_in_strings_with_simple_quotes(
        self,
    ) -> None:
        """
        Given: Code with a string that contains a #
        When: fix_code is run
        Then: The string is left unchanged
        """
        source = dedent(
            """\
            ---
            project: 'Here # is not a comment marker'
            """
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_respects_comment_symbol_in_strings_with_double_quotes(
        self,
    ) -> None:
        """
        Given: Code with a string that contains a #
        When: fix_code is run
        Then: The string is left unchanged
        """
        source = dedent(
            """\
            ---
            project: "Here # is not a comment marker"
            """
        )
        desired_source = dedent(
            """\
            ---
            project: 'Here # is not a comment marker'
            """
        )

        result = fix_code(source)

        assert result == desired_source

    def test_fix_code_respects_jinja_variables_with_equals(
        self,
    ) -> None:
        """
        Given: Code with a long string that contains a jinja variable after an equal
        When: fix_code is run
        Then: The jinja string is not broken
        """
        source = (
            "---\n"
            "environment:\n"
            "  - SUPER_LONG_VARIABLE={{ this_is_a_super_long_long_long_long_long"
            "_variable_name }}\n"
        )

        result = fix_code(source)

        assert result == source

    def test_fix_code_respects_many_jinja_variables(
        self,
    ) -> None:
        """
        Given: Code with a long string that contains two jinja variables
        When: fix_code is run
        Then: The jinja string is not broken
        """
        source = (
            "---\n"
            "project: This is a long long {{ variable_1 }} line that should not be "
            "split on the jinja {{ variable_2 }}"
        )
        desired_source = (
            "---\n"
            "project: This is a long long {{ variable_1 }} line that should not be "
            "split on the\n"
            "  jinja {{ variable_2 }}\n"
        )

        result = fix_code(source)

        assert result == desired_source

    def test_fix_code_respects_jinja_variables_with_operations(
        self,
    ) -> None:
        """
        Given: Code with a long string that contains a jinja variable with operations
        When: fix_code is run
        Then: The jinja string is not broken
        """
        source = (
            "---\n"
            "project: This is a long long long long line that should not be split on "
            "the jinja {{ variable that contains different words }}"
        )
        desired_source = (
            "---\n"
            "project: This is a long long long long line that should not be split on "
            "the jinja\n"
            "  {{ variable that contains different words }}\n"
        )

        result = fix_code(source)

        assert result == desired_source

    def test_fix_code_doesnt_remove_variable(
        self,
    ) -> None:
        """
        Given: Code with a short jinja variable
        When: fix_code is run
        Then: The jinja string is not removed
        """
        source = "---\npath: '{{ item }}'\n"

        result = fix_code(source)

        assert result == source

    @pytest.mark.parametrize(
        ("source", "config", "desired_source"),
        [
            (
                dedent(
                    """\
                    ---
                    list: [item, item]


                    # Comment: desired: 1 line (default) before this comment
                    key: value
                    """
                ),
                None,
                dedent(
                    """\
                    ---
                    list: [item, item]

                    # Comment: desired: 1 line (default) before this comment
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]



                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=1),
                dedent(
                    """\
                    ---
                    list: [item, item]
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]



                    key: value  # Comment: desired: No lines between `list` and `key`
                    """
                ),
                YamlfixConfig(comments_whitelines=0),
                dedent(
                    """\
                    ---
                    list: [item, item]
                    key: value  # Comment: desired: No lines between `list` and `key`
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]



                    key: value  # Comment: desired: No lines between `list` and `key`
                    """
                ),
                YamlfixConfig(comments_whitelines=1),
                dedent(
                    """\
                    ---
                    list: [item, item]
                    key: value  # Comment: desired: No lines between `list` and `key`
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]



                    key: value  # Comment: desired: No lines between `list` and `key`
                    """
                ),
                YamlfixConfig(comments_whitelines=2),
                dedent(
                    """\
                    ---
                    list: [item, item]
                    key: value  # Comment: desired: No lines between `list` and `key`
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]


                    # Comment: desired: 1 line before this comment
                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=1),
                dedent(
                    """\
                    ---
                    list: [item, item]

                    # Comment: desired: 1 line before this comment
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]


                    # Comment: desired: 0 line before this comment
                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=0),
                dedent(
                    """\
                    ---
                    list: [item, item]
                    # Comment: desired: 0 line before this comment
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]


                    # Comment: desired: 2 lines before this comment
                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=2),
                dedent(
                    """\
                    ---
                    list: [item, item]


                    # Comment: desired: 2 lines before this comment
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list: [item, item]

                    # Comment: desired: 2 lines before this comment
                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=2),
                dedent(
                    """\
                    ---
                    list: [item, item]


                    # Comment: desired: 2 lines before this comment
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list:
                      - item
                      # Comment: desired: 0 new line before this comment
                      - item

                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=1),
                dedent(
                    """\
                    ---
                    list:
                      - item
                      # Comment: desired: 0 new line before this comment
                      - item
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list:
                      - item
                      # Comment: desired: 0 new line before this comment
                      - item

                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=0),
                dedent(
                    """\
                    ---
                    list:
                      - item
                      # Comment: desired: 0 new line before this comment
                      - item
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list:
                      - item
                      # Comment: desired: 0 new line before this comment
                      - item

                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=2),
                dedent(
                    """\
                    ---
                    list:
                      - item
                      # Comment: desired: 0 new line before this comment
                      - item
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list:
                      - item

                      # Comment: desired: 1 new line before this comment
                      - item

                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=1),
                dedent(
                    """\
                    ---
                    list:
                      - item

                      # Comment: desired: 1 new line before this comment
                      - item
                    key: value
                    """
                ),
            ),
            (
                dedent(
                    """\
                    ---
                    list:
                      - item

                      # Comment: desired: 2 new lines before this comment
                      - item

                    key: value
                    """
                ),
                YamlfixConfig(comments_whitelines=2),
                dedent(
                    """\
                    ---
                    list:
                      - item


                      # Comment: desired: 2 new lines before this comment
                      - item
                    key: value
                    """
                ),
            ),
        ],
    )
    def test_fix_code_fix_whitelines(
        self,
        source: str,
        config: Optional[YamlfixConfig],
        desired_source: str,
    ) -> None:
        """
        Given: Code with extra whitelines
        When: fix_code is run
        Then: The string has extra whitelines removed
        """
        result = fix_code(source_code=source, config=config)

        assert result == desired_source
