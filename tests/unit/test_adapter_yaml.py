"""Test the Yaml and YamlRoundTrip adapters."""

from textwrap import dedent

import pytest
from ruyaml.constructor import DuplicateKeyError

from yamlfix.model import YamlfixConfig, YamlNodeStyle
from yamlfix.services import fix_code

none_representations = [
    "",
    "null",
    "Null",
    "NULL",
    "~",
]

quote_representations = [
    "'",
    '"',
]


class TestYamlAdapter:
    """Test the Yaml and YamlRoundTrip adapters."""

    def test_indentation_config(self) -> None:
        """Make indentation values configurable."""
        source = dedent(
            """\
            project_name: yamlfix
            list:
              - item
            map:
              key: value
            """
        )
        fixed_source = dedent(
            """\
            ---
            project_name: yamlfix
            list:
                -   item
            map:
                key: value
            """
        )
        config = YamlfixConfig()
        config.indent_offset = 4
        config.indent_mapping = 4
        config.indent_sequence = 8
        config.sequence_style = YamlNodeStyle.KEEP_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_dont_allow_duplicate_keys_config(self) -> None:
        """Test if duplicate keys cause an exception when configured."""
        source = dedent(
            """\
            ---
            project_name: yamlfix
            project_name: yumlfax
            """
        )
        config = YamlfixConfig()
        config.allow_duplicate_keys = False

        with pytest.raises(
            DuplicateKeyError, match='found duplicate key "project_name"'
        ):
            fix_code(source, config)

    def test_comment_spacing_config(self) -> None:
        """Test if spaces are added to comment start if configured."""
        source = dedent(
            """\
            ---
            # comment
            project_name: yamlfix #comment
            """
        )
        fixed_source = dedent(
            """\
            ---
            # comment
            project_name: yamlfix  # comment
            """
        )
        config = YamlfixConfig()
        config.comments_min_spaces_from_content = 2
        config.comments_require_starting_space = True

        result = fix_code(source, config)

        assert result == fixed_source

    def test_dont_generate_explicit_start(self) -> None:
        """Test if the explicit yaml document start indicator is removed\
            when configured."""
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

    def test_if_line_length_expands(self) -> None:
        """Test if configurable line-length expands string value."""
        source = dedent(
            """\
            key: value value value value value value
              value value value value value value
              value value value value value value
              value value value value value value
              value value value value value value
              value value value value value value
            """
        )
        fixed_source = dedent(
            """\
            ---
            key: value value value value value value value value value value value value value value value value value
              value value value value value value value value value value value value value value value value value
              value value
            """  # noqa: E501
        )
        config = YamlfixConfig()
        config.line_length = 100

        result = fix_code(source, config)

        assert result == fixed_source

    def test_if_line_length_contracts(self) -> None:
        """Test if configurable line-length contracts string value."""
        source = dedent(
            """\
            key: value value value value value value
              value value value value value value
              value value value value value value
              value value value value value value
              value value value value value value
              value value value value value value
            """
        )
        fixed_source = dedent(
            """\
            ---
            key: value value value
              value value value value
              value value value value
              value value value value
              value value value value
              value value value value
              value value value value
              value value value value
              value value value value
              value
            """
        )
        config = YamlfixConfig()
        config.line_length = 20

        result = fix_code(source, config)

        assert result == fixed_source

    @pytest.mark.parametrize("none_representation", none_representations)
    def test_none_representation_config(self, none_representation: str) -> None:
        """Make `none` value representations configurable."""
        source = dedent(
            """\
            none1:
            none2: null
            none3: Null
            none4: NULL
            none5: ~
            """
        )
        fixed_none_representation = f" {none_representation}"
        if none_representation == "":
            fixed_none_representation = ""
        fixed_source = dedent(
            f"""\
            ---
            none1:{fixed_none_representation}
            none2:{fixed_none_representation}
            none3:{fixed_none_representation}
            none4:{fixed_none_representation}
            none5:{fixed_none_representation}
            """
        )
        config = YamlfixConfig()
        config.none_representation = none_representation

        result = fix_code(source, config)

        assert result == fixed_source

    def test_preserve_quotes_config(self) -> None:
        """Make it configurable. That quotes are preserved"""
        source = dedent(
            """\
            ---
            str_key1: "value"
            str_key2: 'value'
            str_key3: value
            """
        )
        config = YamlfixConfig()
        config.preserve_quotes = True

        result = fix_code(source, config)

        assert result == source

    @pytest.mark.parametrize("quote_representation", quote_representations)
    def test_quote_all_keys_and_values_config(self, quote_representation: str) -> None:
        """Quote all keys and values with configurable quote representation."""
        source = dedent(
            """\
            none_key: null
            bool_key: true
            int_key: 1
            str_key1: "value"
            str_key2: 'value'
            str_key3: value
            str_multiline: |
              value
              value
            complex_key:
              complex_key2: value
              list:
                - item1
                - item2
              complex_list:
                - item1
                - complex_item:
                    key: value
            """
        )
        quote = quote_representation
        fixed_source = dedent(
            f"""\
            ---
            {quote}none_key{quote}:
            {quote}bool_key{quote}: true
            {quote}int_key{quote}: 1
            {quote}str_key1{quote}: {quote}value{quote}
            {quote}str_key2{quote}: {quote}value{quote}
            {quote}str_key3{quote}: {quote}value{quote}
            {quote}str_multiline{quote}: |
              value
              value
            {quote}complex_key{quote}:
              {quote}complex_key2{quote}: {quote}value{quote}
              {quote}list{quote}: [{quote}item1{quote}, {quote}item2{quote}]
              {quote}complex_list{quote}:
                - {quote}item1{quote}
                - {quote}complex_item{quote}:
                    {quote}key{quote}: {quote}value{quote}
            """
        )
        config = YamlfixConfig()
        config.quote_representation = quote_representation
        config.quote_keys_and_basic_values = True

        result = fix_code(source, config)

        assert result == fixed_source

    @pytest.mark.parametrize("quote_representation", quote_representations)
    def test_quote_values_config(self, quote_representation: str) -> None:
        """Quote only scalar values with configurable quote representation."""
        source = dedent(
            """\
            none_key: null
            bool_key: true
            int_key: 1
            str_key1: "value"
            str_key2: 'value'
            str_key3: value
            str_multiline: |
              value
              value
            complex_key:
              complex_key2: value
              list:
                - item1
                - item2
              complex_list:
                - item1
                - complex_item:
                    key: 'value?'
            """
        )
        quote = quote_representation
        fixed_source = dedent(
            f"""\
            ---
            none_key:
            bool_key: true
            int_key: 1
            str_key1: {quote}value{quote}
            str_key2: {quote}value{quote}
            str_key3: {quote}value{quote}
            str_multiline: |
              value
              value
            complex_key:
              complex_key2: {quote}value{quote}
              list: [{quote}item1{quote}, {quote}item2{quote}]
              complex_list:
                - item1
                - complex_item:
                    key: {quote}value?{quote}
            """
        )
        config = YamlfixConfig()
        config.quote_representation = quote_representation
        config.quote_basic_values = True

        result = fix_code(source, config)

        assert result == fixed_source

    @pytest.mark.parametrize("quote_representation", quote_representations)
    def test_quote_all_keys_and_values_config_and_preserve_quotes(
        self, quote_representation: str
    ) -> None:
        """Quote all keys and values with configurable quote representation. \
           `quote_keys_and_basic_values` in combination with `preserve_quotes`"""
        source = dedent(
            """\
            none_key: null
            bool_key: true
            int_key: 1
            str_key1: "value"
            str_key2: 'value'
            str_key3: value
            str_multiline: |
              value
              value
            complex_key:
              complex_key2: value
              list:
                - item1
                - item2
              complex_list:
                - item1
                - complex_item:
                    key: value
            """
        )
        quote = quote_representation
        fixed_source = dedent(
            f"""\
            ---
            {quote}none_key{quote}:
            {quote}bool_key{quote}: true
            {quote}int_key{quote}: 1
            {quote}str_key1{quote}: "value"
            {quote}str_key2{quote}: 'value'
            {quote}str_key3{quote}: {quote}value{quote}
            {quote}str_multiline{quote}: |
              value
              value
            {quote}complex_key{quote}:
              {quote}complex_key2{quote}: {quote}value{quote}
              {quote}list{quote}: [{quote}item1{quote}, {quote}item2{quote}]
              {quote}complex_list{quote}:
                - {quote}item1{quote}
                - {quote}complex_item{quote}:
                    {quote}key{quote}: {quote}value{quote}
            """
        )
        config = YamlfixConfig()
        config.quote_representation = quote_representation
        config.quote_keys_and_basic_values = True
        config.preserve_quotes = True

        result = fix_code(source, config)

        assert result == fixed_source

    @pytest.mark.parametrize("quote_representation", quote_representations)
    def test_quote_values_config_and_preserve_quotes(
        self, quote_representation: str
    ) -> None:
        """Quote only scalar values with configurable quote representation. \
           `quote_basic_values` in combination with `preserve_quotes`"""
        source = dedent(
            """\
            none_key: null
            bool_key: true
            int_key: 1
            str_key1: "value"
            str_key2: 'value'
            str_key3: value
            str_multiline: |
              value
              value
            complex_key:
              complex_key2: value
              list:
                - item1
                - item2
              complex_list:
                - item1
                - complex_item:
                    key: 'value?'
            """
        )
        quote = quote_representation
        fixed_source = dedent(
            f"""\
            ---
            none_key:
            bool_key: true
            int_key: 1
            str_key1: "value"
            str_key2: 'value'
            str_key3: {quote}value{quote}
            str_multiline: |
              value
              value
            complex_key:
              complex_key2: {quote}value{quote}
              list: [{quote}item1{quote}, {quote}item2{quote}]
              complex_list:
                - item1
                - complex_item:
                    key: 'value?'
            """
        )
        config = YamlfixConfig()
        config.quote_representation = quote_representation
        config.quote_basic_values = True
        config.preserve_quotes = True

        result = fix_code(source, config)

        assert result == fixed_source

    def test_sequence_flow_style_config(self) -> None:
        """Make inline list style 'flow-style' configurable."""
        source = dedent(
            """\
            list:
              - item
              - item
            list2: [item, item]
            """
        )
        fixed_source = dedent(
            """\
            ---
            list: [item, item]
            list2: [item, item]
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.FLOW_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_sequence_block_style_config(self) -> None:
        """Make multi-line list style 'block-style' configurable."""
        source = dedent(
            """\
            list:
              - item
              - item
            list2: [item, item]
            """
        )
        fixed_source = dedent(
            """\
            ---
            list:
              - item
              - item
            list2:
              - item
              - item
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.BLOCK_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_sequence_keep_style_config(self) -> None:
        """Make it configurable, that the list style is not changed and keeps\
            the original flow- or block-style for sequences."""
        source = dedent(
            """\
            ---
            list:
              - item
              - item
            list2: [item, item]
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.KEEP_STYLE

        result = fix_code(source, config)

        assert result == source

    def test_sequence_block_style_enforcement_for_lists_with_comments(self) -> None:
        """Fall back to multi-line list style 'block-style' if list contains comments,\
            even if flow-style is selected."""
        source = dedent(
            """\
            list: # List comment
              # Comment 1
              - item
              # Comment 2
              - item
            list2: # List 2 Comment
              - item
              - item
            list3: # List 3 Comment
              - item with long description
              - item with long description
              - item with long description
              - item with long description
            """
        )
        fixed_source = dedent(
            """\
            ---
            list:  # List comment
              # Comment 1
              - item
              # Comment 2
              - item
            list2: [item, item]  # List 2 Comment
            list3:  # List 3 Comment
              - item with long description
              - item with long description
              - item with long description
              - item with long description
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.FLOW_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_sequence_block_style_enforcement_for_lists_with_non_scalar_values(
        self,
    ) -> None:
        """Fall back to multi-line list style 'block-style' if list contains non-scalar\
            values, like other lists or dicts, even if flow-style is selected."""
        source = dedent(
            """\
            list:
              - nested_list:
                  - item
              - item
            list2:
              - item
              - nested_dict:
                  key: value
            list3:
              - item
              - item
            """
        )
        fixed_source = dedent(
            """\
            ---
            list:
              - nested_list: [item]
              - item
            list2:
              - item
              - nested_dict:
                  key: value
            list3: [item, item]
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.FLOW_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_sequence_block_style_enforcement_for_lists_longer_than_line_length(
        self,
    ) -> None:
        """Fall back to multi-line list style 'block-style' if list would be longer than\
            line_length, even if flow-style is selected."""
        source = dedent(
            """\
            looooooooooooooooooooooooooooooooooooongKey:
              - item
            list:
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
            list2:
              - item
              - item
              - item
            """
        )
        fixed_source = dedent(
            """\
            ---
            looooooooooooooooooooooooooooooooooooongKey:
              - item
            list:
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
              - loooooooooooooooooooongItem
            list2: [item, item, item]
            """
        )
        config = YamlfixConfig()
        config.line_length = 40
        config.sequence_style = YamlNodeStyle.FLOW_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_sequence_flow_style_with_trailing_newlines(self) -> None:
        """Correct flow-style lists that have trailing newlines.

        Without this fix the following block-style list:
        ```
        list:
          - item
          - item



        key: value
        ```

        is converted to this weird-looking flow-style list:
        ```
        list: [item, item



        ]
        key: value
        ```

        instead of
        ```
        list: [item, item]



        key: value
        ```
        """
        source = dedent(
            """\
            list:
              - item
              - item



            key: value
            """
        )
        fixed_source = dedent(
            """\
            ---
            list: [item, item]
            key: value
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.FLOW_STYLE

        result = fix_code(source, config)

        assert result == fixed_source

    def test_empty_list_inline_comment_indentation(self) -> None:
        """Check if inline comment is preserved for empty lists with comments."""
        source = dedent(
            """\
            ---
            indented:
              key: value
              list1: [value]  # comment with value
              list2: []
              list3: []  # comment on the same line as empty list
              map:
                anotherKey: anotherValue
            """
        )
        config = YamlfixConfig()
        config.sequence_style = YamlNodeStyle.FLOW_STYLE

        result = fix_code(source, config)

        assert result == source

    def test_section_whitelines(self) -> None:
        """Check if section whitelines are preserved."""
        source = dedent(
            # pylint: disable=C0303
            """\
            ---

            begin_section:
              key: value
            key1: value

            key2: value

            happy_path_section:
              key1: value

              key2: value
              nested_dict:
                nested_key: value

            # Comment 1
            # Comment 2
            comment_section:
                key: value
            key3: value
            key4: value

            key5: value
            close_section:
                key: value



            """  # noqa: W291
        )
        fixed_source = dedent(
            """\
            ---
            begin_section:
              key: value

            key1: value
            key2: value

            happy_path_section:
              key1: value
              key2: value
              nested_dict:
                nested_key: value


            # Comment 1
            # Comment 2
            comment_section:
              key: value

            key3: value
            key4: value
            key5: value

            close_section:
              key: value
            """
        )
        config = YamlfixConfig()
        config.section_whitelines = 1
        config.comments_whitelines = 2

        result = fix_code(source, config)

        assert result == fixed_source

    def test_section_whitelines_begin_no_explicit_start(self) -> None:
        """Check that no whitelines are added at start of file when explicit start \
            is not applied."""
        source = dedent(
            # pylint: disable=C0303
            """\
            begin_section:
              key: value
            """  # noqa: W291
        )
        fixed_source = dedent(
            """\
            begin_section:
              key: value
            """
        )
        config = YamlfixConfig()
        config.section_whitelines = 1
        config.comments_whitelines = 2
        config.explicit_start = False

        result = fix_code(source, config)

        assert result == fixed_source

    def test_whitelines_collapsed(self) -> None:
        """Checks that whitelines are collapsed by default."""
        source = dedent(
            """\
            key: value

            dict:
              key: value
              nested_dict:
                - key: value
                  key2: value2

                - key: value
            """
        )
        fixed_source = dedent(
            """\
            ---
            key: value
            dict:
              key: value
              nested_dict:
                - key: value
                  key2: value2
                - key: value
            """
        )
        config = YamlfixConfig()

        result = fix_code(source, config)

        assert result == fixed_source

    def test_whitelines_adjusted_to_value(self) -> None:
        """Checks that amount of whitelines are in line with the config value."""
        source = dedent(
            """\
            key: value

            dict:
              key: value


              nested_list:
                - key: value
                  key2: value2

                - key: value
            """
        )
        fixed_source = dedent(
            """\
            ---
            key: value

            dict:
              key: value

              nested_list:
                - key: value
                  key2: value2

                - key: value
            """
        )
        config = YamlfixConfig()
        config.whitelines = 1

        result = fix_code(source, config)

        assert result == fixed_source

    def test_whitelines_higher_than_secion_whitelines(self) -> None:
        """Checks that amount of whitelines are in line with the config values."""
        source = dedent(
            # pylint: disable=C0303
            """\
            ---
            begin_section:
              key: value
            key1: value

            key2: value
            happy_path_section:
              key1: value

              key2: value
              nested_dict:
                nested_key: value

            # Comment 1
            # Comment 2
            comment_section:
                key: value
            key3: value
            key4: value

            key5: value
            close_section:
                key: value



            """  # noqa: W291
        )
        fixed_source = dedent(
            """\
            ---
            begin_section:
              key: value


            key1: value

            key2: value


            happy_path_section:
              key1: value

              key2: value
              nested_dict:
                nested_key: value

            # Comment 1
            # Comment 2
            comment_section:
              key: value


            key3: value
            key4: value

            key5: value


            close_section:
              key: value
            """
        )
        config = YamlfixConfig()
        config.whitelines = 1
        config.section_whitelines = 2

        result = fix_code(source, config)

        assert result == fixed_source

    def test_enforcing_flow_style_together_with_adjustable_newlines(self) -> None:
        """Checks that transforming block style sequences to flow style together with
        newlines adjusting produces correct result.
        """
        source = dedent(
            """\
            ---
            dict:
              nested_dict:
                key: value
                key2:
                  - list_item


              nested_dict2:
                key: value
            """
        )
        fixed_source = dedent(
            """\
            ---
            dict:
              nested_dict:
                key: value
                key2: [list_item]

              nested_dict2:
                key: value
            """
        )
        config = YamlfixConfig()
        config.whitelines = 1
        config.sequence_style = YamlNodeStyle.FLOW_STYLE

        result = fix_code(source, config)

        assert result == fixed_source
