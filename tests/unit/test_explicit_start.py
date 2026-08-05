"""Test explicit_start configuration behavior."""

from textwrap import dedent

from yamlfix.model import YamlfixConfig
from yamlfix.services import fix_code


class TestExplicitStartFalse:
    """Tests for explicit_start = False."""

    def test_removes_leading_start_marker(self) -> None:
        """When explicit_start is False, leading --- is removed."""
        source = dedent(
            """\
            ---
            project_name: yamlfix
            """
        )
        fixed_source = dedent(
            """\
            project_name: yamlfix
            """
        )
        config = YamlfixConfig()
        config.explicit_start = False

        result = fix_code(source, config)

        assert result == fixed_source

    def test_preserves_inter_document_separators(self) -> None:
        """When explicit_start is False, inter-document --- separators are preserved."""
        source = dedent(
            """\
            ---
            name: doc1
            ---
            name: doc2
            """
        )
        config = YamlfixConfig()
        config.explicit_start = False

        result = fix_code(source, config)

        # The inter-document separator must remain (structurally required)
        assert "---\nname: doc2" in result

    def test_multi_document_three_docs(self) -> None:
        """When explicit_start is False, all inter-document separators are preserved."""
        source = dedent(
            """\
            ---
            name: doc1
            ---
            name: doc2
            ---
            name: doc3
            """
        )
        config = YamlfixConfig()
        config.explicit_start = False

        result = fix_code(source, config)

        # Inter-document separators must remain (at least 2 for 3 docs)
        assert result.count("---") >= 2


class TestExplicitStartTrue:
    """Tests for explicit_start = True."""

    def test_adds_start_marker(self) -> None:
        """When explicit_start is True, --- is added."""
        source = dedent(
            """\
            project_name: yamlfix
            """
        )
        fixed_source = dedent(
            """\
            ---
            project_name: yamlfix
            """
        )
        config = YamlfixConfig()
        config.explicit_start = True

        result = fix_code(source, config)

        assert result == fixed_source

    def test_multi_document_preserves_separators(self) -> None:
        """Multi-document files keep --- dividers with explicit_start=True."""
        source = dedent(
            """\
            ---
            name: doc1
            ---
            name: doc2
            """
        )
        config = YamlfixConfig()
        config.explicit_start = True

        result = fix_code(source, config)

        # Both documents should have separators
        assert result.count("---") >= 2
