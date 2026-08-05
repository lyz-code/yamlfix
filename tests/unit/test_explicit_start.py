"""Test explicit_start configuration behavior."""

from textwrap import dedent

from yamlfix.model import YamlfixConfig
from yamlfix.services import fix_code


class TestExplicitStartNone:
    """Tests for explicit_start = None (leave as-is)."""

    def test_preserves_existing_start_marker(self) -> None:
        """When explicit_start is None, existing --- at start is preserved."""
        source = dedent(
            """\
            ---
            project_name: yamlfix
            """
        )
        config = YamlfixConfig()
        config.explicit_start = None

        result = fix_code(source, config)

        assert result == source

    def test_does_not_add_start_marker(self) -> None:
        """When explicit_start is None, --- is not added to files without it."""
        source = dedent(
            """\
            project_name: yamlfix
            """
        )
        config = YamlfixConfig()
        config.explicit_start = None

        result = fix_code(source, config)

        assert result == source


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


class TestMultiDocumentSeparators:
    """Tests for multi-document YAML files."""

    def test_multi_document_preserves_separators_with_none(self) -> None:
        """Multi-document files always keep --- dividers with explicit_start=None."""
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
        config.explicit_start = None

        result = fix_code(source, config)

        # All inter-document separators must be present
        assert result.count("---") >= 2  # At least 2 separators between 3 docs

    def test_multi_document_preserves_separators_with_true(self) -> None:
        """Multi-document files always keep --- dividers with explicit_start=True."""
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

    def test_multi_document_preserves_separators_with_false(self) -> None:
        """Multi-document files always keep --- dividers with explicit_start=False."""
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

        # Inter-document separator must remain even with explicit_start=False
        assert "---" in result
