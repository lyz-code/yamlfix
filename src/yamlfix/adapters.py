"""Define adapter / helper classes to hide unrelated functionality in."""

import logging
import re
from functools import partial
from io import StringIO
from typing import Any, Callable, List, Match, Optional, Tuple

from ruyaml.main import YAML
from ruyaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from ruyaml.representer import RoundTripRepresenter
from ruyaml.tokens import CommentToken

from yamlfix.model import YamlfixConfig, YamlNodeStyle

log = logging.getLogger(__name__)


class Yaml:
    """Adapter that holds the configured ruaml yaml fixer."""

    def __init__(self, config: Optional[YamlfixConfig]) -> None:
        """Initialize the yaml adapter with an optional yamlfix config.

        Args:
            config: Small set of user provided configuration options for yamlfix.
        """
        self.yaml = YAML()
        self.config = config or YamlfixConfig()

        # we have to call setattr with the string value, because the internal ruyaml
        # implementation does the same thing and does not expose the attribute itself
        setattr(  # noqa: B010
            self.yaml,
            "_representer",
            YamlfixRepresenter(
                self.config,
                self.yaml.default_style,
                self.yaml.default_flow_style,
                self.yaml,
            ),
        )

        self._base_configuration()

    def _base_configuration(self) -> None:
        """Configure base settings for Ruamel's yaml."""
        log.debug("Running ruamel yaml base configuration...")
        config = self.config

        # Configure YAML formatter
        self.yaml.indent(
            mapping=config.indent_mapping,
            sequence=config.indent_sequence,
            offset=config.indent_offset,
        )
        self.yaml.allow_duplicate_keys = config.allow_duplicate_keys

        # Start the document with ---
        # ignore: variable has type None, what can we do, it doesn't have type hints...
        self.yaml.explicit_start = config.explicit_start  # type: ignore
        self.yaml.width = config.line_length  # type: ignore
        self.yaml.preserve_quotes = config.preserve_quotes  # type: ignore


class YamlfixRepresenter(RoundTripRepresenter):
    """Yamlfix's custom implementation of the ruyaml.RoundTripRepresenter\
        that can be configured with YamlfixConfig."""

    def __init__(
        self,
        config: YamlfixConfig,
        default_style: Optional[str] = None,
        default_flow_style: Optional[bool] = None,
        dumper: Optional[YAML] = None,
    ) -> None:
        """Initialize the YamlfixRepresenter and its parent RoundTripRepresenter."""
        RoundTripRepresenter.__init__(
            self,
            default_style=default_style,
            default_flow_style=default_flow_style,
            dumper=dumper,
        )

        self.config: YamlfixConfig = config
        self.patch_functions: List[Callable[[Node, Node], None]] = []

        configure_patch_functions = [
            self._configure_quotation_for_basic_values,
            self._configure_sequence_style,
        ]

        for patch_configurer in configure_patch_functions:
            patch_configurer()

    def represent_none(self, data: Any) -> ScalarNode:  # noqa: ANN401
        """Configure how Ruamel's yaml represents None values.

        Default is an empty representation, could be overridden by canonical values
        like "~", "null", "NULL"
        """
        if (
            self.config.none_representation is None
            or self.config.none_representation == ""
        ):
            return super().represent_none(data)

        return self.represent_scalar(
            "tag:yaml.org,2002:null", self.config.none_representation
        )

    def represent_str(self, data: Any) -> ScalarNode:  # noqa: ANN401
        """Configure Ruamel's yaml fixer to quote all yaml keys and simple* string values.

        Simple string values meaning: No multi line strings, as they are represented
        by LiteralScalarStrings instead.
        """
        if (
            not self.config.quote_keys_and_basic_values
            or self.config.quote_representation is None
        ):
            return super().represent_str(data)

        return self.represent_scalar(
            "tag:yaml.org,2002:str", data, self.config.quote_representation
        )

    def represent_mapping(
        self, tag: Any, mapping: Any, flow_style: Optional[Any] = None  # noqa: ANN401
    ) -> MappingNode:
        """Modify / Patch the original ruyaml representer represent_mapping value and\
            call the provided patch_function on its mapping_values."""
        mapping_node: MappingNode = super().represent_mapping(tag, mapping, flow_style)
        mapping_values: List[Tuple[ScalarNode, Node]] = mapping_node.value

        if isinstance(mapping_values, list):
            for mapping_value in mapping_values:
                if isinstance(mapping_value, tuple):
                    key_node: Node = mapping_value[0]
                    value_node: Node = mapping_value[1]
                    for patch_function in self.patch_functions:
                        patch_function(key_node, value_node)

        return mapping_node

    def _configure_quotation_for_basic_values(self) -> None:
        """Configure Ruamel's yaml fixer to quote only simple* yaml string values.

        Simple string values meaning: Any string that does not already have an
        explicit 'style' applied already -> multi line strings have a style value
        of "|" per default.
        """
        config = self.config
        log.debug("Setting up ruamel yaml 'quote simple values' configuration...")

        def patch_quotations(key_node: Node, value_node: Node) -> None:  # noqa: W0613
            if not config.quote_basic_values or config.quote_representation is None:
                return

            # if this is a scalar value node itself, apply the quotations now
            self._apply_simple_value_quotations(value_node)

            # if this is a sequence value node, check for value presence, complex
            # sequences and apply quotations to its values
            if not isinstance(value_node, SequenceNode) or value_node.value is None:
                return

            sequence_node: SequenceNode = value_node

            if self._seq_contains_non_scalar_nodes(
                sequence_node
            ) or self._seq_contains_non_empty_comments(sequence_node):
                return

            for seq_value in sequence_node.value:
                self._apply_simple_value_quotations(seq_value)

        self.patch_functions.append(patch_quotations)

    def _configure_sequence_style(self) -> None:
        """Configure Ruamel's yaml fixer to represent lists as either block-style \
            or flow-style.

        Also make sure, that lists containing non-scalar values (other maps, \
            lists), lists that contain comments and lists that would breach the
            line-length are forced to block-style, regardless of configuration.

        Lists in block-style look like this:
        ```
        list:
          # Comment for item
          - item
          - item
          - complex_item:
              # Comment for key
              key: value
        ```

        Lists in flow-style look like this, we do not convert lists with complex
        values or lists with comments to that style, it is meant for simple lists,
        that contain only scalar values (string, int, bool, etc.) not other complex
        values (lists, dicts, comments, etc.)
        ```
        list: [item, item, item]
        ```

        Empty lists are not handled well in either style, so they are skipped as well,
        as you can only represent empty lists in flow-style either way.
        """
        config = self.config
        log.debug("Setting up ruamel yaml 'sequence flow style' configuration...")

        def patch_sequence_style(key_node: Node, value_node: Node) -> None:
            if isinstance(key_node, ScalarNode) and isinstance(
                value_node, SequenceNode
            ):
                # don't modify the sequence style at all, if the config value is
                # set to `keep_style`
                if config.sequence_style == YamlNodeStyle.KEEP_STYLE:
                    return

                force_block_style: bool = False
                sequence_node: SequenceNode = value_node

                # check if the sequence node value is present and if it is not empty
                if not sequence_node.value:
                    return

                # if this sequence contains non-scalar nodes (i.e. dicts, lists, etc.),
                # force block-style
                force_block_style = (
                    force_block_style
                    or self._seq_contains_non_scalar_nodes(sequence_node)
                )

                # if this sequence contains non-empty comments, force block-style
                force_block_style = (
                    force_block_style
                    or self._seq_contains_non_empty_comments(sequence_node)
                )

                # if this sequence, rendered in flow-style would breach the line-width,
                # force block-style roughly calculate the consumed width, in any case
                # ruyaml will fold flow-style lists if they breach the limit only
                # consider scalars, as non-scalar nodes should force block-style already
                force_block_style = (
                    force_block_style
                    or self._seq_length_longer_than_line_length(key_node, sequence_node)
                )

                sequence_node.flow_style = (
                    config.sequence_style == YamlNodeStyle.FLOW_STYLE
                )
                if force_block_style:
                    sequence_node.flow_style = False

        self.patch_functions.append(patch_sequence_style)

    @staticmethod
    def _seq_contains_non_scalar_nodes(seq_node: Node) -> bool:
        return any(not isinstance(node, ScalarNode) for node in seq_node.value)

    @staticmethod
    def _seq_contains_non_empty_comments(seq_node: Node) -> bool:
        comment_tokens: List[CommentToken] = []

        for node in seq_node.value:
            if isinstance(node, ScalarNode) and isinstance(node.comment, list):
                comment_tokens.extend(node.comment)

        return any(
            isinstance(comment_token, CommentToken)
            and comment_token.value.strip() != ""
            for comment_token in comment_tokens
        )

    def _seq_length_longer_than_line_length(
        self, key_node: Node, seq_node: Node
    ) -> bool:
        config = self.config

        # This could be made configurable, or rather we could calculate if we need
        # the quotation spaces for the configured settings, but if we err on the
        # side of caution we can always force block-mode even for values that could
        # technically, without quotes, fit into the line-length

        # quotation marks around scalar value
        quote_length: int = 2

        # comma and space between scalar values or colon and space
        # between key + values
        separator_length: int = 2

        # opening and closing brackets that should fit on the same line
        bracket_length: int = 2

        key_length: int = len(str(key_node.value)) + quote_length + separator_length

        scalar_length: int = 0

        for node in seq_node.value:
            if isinstance(node, ScalarNode):
                scalar_length += len(str(node.value)) + quote_length + separator_length

        if key_length + scalar_length + bracket_length > config.line_length:
            return True

        return False

    def _apply_simple_value_quotations(self, value_node: Node) -> None:
        if (
            isinstance(value_node, ScalarNode)
            and value_node.tag == "tag:yaml.org,2002:str"
            and value_node.style is None
        ):
            value_node.style = self.config.quote_representation


YamlfixRepresenter.add_representer(type(None), YamlfixRepresenter.represent_none)
YamlfixRepresenter.add_representer(str, YamlfixRepresenter.represent_str)


class SourceCodeFixer:
    """Adapter that holds all source code yaml fixers."""

    def __init__(self, yaml: Yaml, config: Optional[YamlfixConfig]) -> None:
        """Initialize the source code fixer adapter with a configured yaml fixer \
            instance and optional yamlfix config.

        Args:
            yaml: Initialized Ruamel formatter to use for source code correction.
            config: Small set of user provided configuration options for yamlfix.
        """
        self.yaml = yaml.yaml
        self.config = config or YamlfixConfig()

    def fix(self, source_code: str) -> str:
        """Run all yaml source code fixers.

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        log.debug("Running source code fixers...")

        fixers = [
            self._fix_truthy_strings,
            self._fix_jinja_variables,
            self._ruamel_yaml_fixer,
            self._restore_truthy_strings,
            self._restore_jinja_variables,
            self._restore_double_exclamations,
            self._fix_comments,
            self._fix_flow_style_lists,
            self._fix_whitelines,
            self._fix_top_level_lists,
            self._add_newline_at_end_of_file,
        ]

        for fixer in fixers:
            source_code = fixer(source_code)

        return source_code

    def _ruamel_yaml_fixer(self, source_code: str) -> str:
        """Run Ruamel's yaml fixer.

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        log.debug("Running ruamel yaml fixer...")
        source_dicts = self.yaml.load_all(source_code)

        # Return the output to a string
        string_stream = StringIO()
        for source_dict in source_dicts:
            self.yaml.dump(source_dict, string_stream)
            source_code = string_stream.getvalue()
        string_stream.close()

        return source_code.strip()

    @staticmethod
    def _fix_top_level_lists(source_code: str) -> str:
        """Deindent the source with a top level list.

        Documents like the following:

        ```yaml
        ---
        # Comment
        - item 1
        - item 2
        ```

        Are wrongly indented by the ruyaml parser:

        ```yaml
        ---
        # Comment
        - item 1
        - item 2
        ```

        This function restores the indentation back to the original.

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        log.debug("Fixing top level lists...")
        source_lines = source_code.splitlines()
        fixed_source_lines: List[str] = []
        is_top_level_list: Optional[bool] = None

        indent: str = ""
        for line in source_lines:
            # Skip the heading and first empty lines
            if re.match(r"^(---|#.*|)$", line):
                fixed_source_lines.append(line)
                continue

            # Check if the first valid line is an indented list item
            if re.match(r"\s*- +.*", line) and is_top_level_list is None:
                is_top_level_list = True

                # Extract the indentation level
                serialized_line = re.match(r"(?P<indent>\s*)- +(?P<content>.*)", line)
                if serialized_line is None:  # pragma: no cover
                    raise ValueError(
                        f"Error extracting the indentation of line: {line}"
                    )
                indent = serialized_line.groupdict()["indent"]

                # Remove the indentation from the line
                fixed_source_lines.append(re.sub(rf"^{indent}(.*)", r"\1", line))
            elif is_top_level_list:
                # ruyaml doesn't change the indentation of comments
                if re.match(r"\s*#.*", line):
                    fixed_source_lines.append(line)
                else:
                    fixed_source_lines.append(re.sub(rf"^{indent}(.*)", r"\1", line))
            else:
                return source_code

        return "\n".join(fixed_source_lines)

    @staticmethod
    def _fix_flow_style_lists(source_code: str) -> str:
        """Fix trailing newlines within flow-style lists.

        Documents like the following:

        ```yaml
        ---
        list: ["a", b, 'c']


        next-element: "d"
        ```

        Are wrongly formatted by the ruyaml parser:

        ```yaml
        ---
        list: ["a", b, 'c'


        ]
        next-element: "d"
        ```

        This function moves the closing bracket to the end of the flow-style
        list definition and positions the newlines after the closing bracket.

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        log.debug("Fixing flow-style lists...")
        pattern = r"\[(?P<items>.*)(?P<newlines>\n+)]"
        replacement = r"[\g<items>]\g<newlines>"
        return re.sub(pattern, repl=replacement, string=source_code)

    @staticmethod
    def _fix_truthy_strings(source_code: str) -> str:
        """Convert common strings that refer to booleans.

        All caps variations of true, yes and on are transformed to true, while false,
        no and off are transformed to false.

        Ruyaml understands these strings and converts them to the lower version of
        the word instead of converting them to true and false.

        [More info](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy) # noqa: E501

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        log.debug("Fixing truthy strings...")
        source_lines = source_code.splitlines()
        fixed_source_lines: List[str] = []

        for line in source_lines:
            line_contains_true = re.match(
                r"(?P<pre_boolean_text>.*(:|-) )(true|yes|on)$", line, re.IGNORECASE
            )
            line_contains_false = re.match(
                r"(?P<pre_boolean_text>.*(:|-) )(false|no|off)$", line, re.IGNORECASE
            )

            if line_contains_true:
                fixed_source_lines.append(
                    f"{line_contains_true.groupdict()['pre_boolean_text']}true"
                )
            elif line_contains_false:
                fixed_source_lines.append(
                    f"{line_contains_false.groupdict()['pre_boolean_text']}false"
                )
            else:
                fixed_source_lines.append(line)

        return "\n".join(fixed_source_lines)

    @staticmethod
    def _restore_truthy_strings(source_code: str) -> str:
        """Restore truthy strings to strings.

        The Ruyaml parser removes the apostrophes of all the caps variations of
        the strings 'yes', 'on', no and 'off' as it interprets them as booleans.

        As this function is run after _fix_truthy_strings, those strings are
        meant to be strings. So we're turning them back from booleans to strings.

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        log.debug("Restoring truthy strings...")
        source_lines = source_code.splitlines()
        fixed_source_lines: List[str] = []

        for line in source_lines:
            line_contains_valid_truthy_string = re.match(
                r"(?P<pre_boolean_text>.*(:|-) )(?P<boolean_text>yes|on|no|off)$",
                line,
                re.IGNORECASE,
            )
            if line_contains_valid_truthy_string:
                fixed_source_lines.append(
                    f"{line_contains_valid_truthy_string.groupdict()['pre_boolean_text']}"  # noqa: E501
                    f"'{line_contains_valid_truthy_string.groupdict()['boolean_text']}'"
                )
            else:
                fixed_source_lines.append(line)

        return "\n".join(fixed_source_lines)

    def _fix_comments(self, source_code: str) -> str:
        log.debug("Fixing comments...")
        config = self.config
        comment_start = " " * config.comments_min_spaces_from_content + "#"

        fixed_source_lines = []

        for line in source_code.splitlines():
            # Comment at the start of the line
            if config.comments_require_starting_space and re.search(r"(^|\s)#\w", line):
                line = line.replace("#", "# ")
            # Comment in the middle of the line, but it's not part of a string
            if (
                config.comments_min_spaces_from_content > 1
                and " #" in line
                and line[-1] not in ["'", '"']
            ):
                line = re.sub(r"(.+\S)(\s+?)#", rf"\1{comment_start}", line)
            fixed_source_lines.append(line)

        return "\n".join(fixed_source_lines)

    def _fix_whitelines(self, source_code: str) -> str:
        """Fixes number of consecutive whitelines.

        Before a line that only includes a comment, either:
          - 0 whiteline is allowed
          - Exactly `self.config.comments_whitelines` whitelines are allowed

        This method also adjusts amount of whitelines that are not immediately followed
        by a comment.

        Args:
            self: Source code to be corrected.

        Returns:
            Source code with appropriate whitelines standards.
        """
        config = self.config
        n_whitelines = config.whitelines
        n_whitelines_from_content = config.comments_whitelines

        re_whitelines_with_comments = "\n\n+[\t ]{0,}[#]"
        re_whitelines_with_no_comments = "\n\n+[\t ]{0,}[^#\n\t ]"

        adjust_whitelines = partial(self._replace_whitelines, n_whitelines=n_whitelines)
        replace_by_n_whitelines = partial(
            self._replace_whitelines,
            n_whitelines=n_whitelines_from_content,
        )

        source_code = re.sub(
            pattern=re_whitelines_with_no_comments,
            repl=adjust_whitelines,
            string=source_code,
        )
        source_code = self._fix_section_whitelines(source_code)
        source_code = re.sub(
            pattern=re_whitelines_with_comments,
            repl=replace_by_n_whitelines,
            string=source_code,
        )

        return source_code

    @staticmethod
    def _replace_whitelines(match: Match[str], n_whitelines: int) -> str:
        """Replaces whitelines by a fixed number, `n_whitelines`, of whitelines.

        Method used by `SourceCodeFixer._fix_whitelines()` to replace whitelines when
        whitelines are not followed by a comment.

        Args:
            match: The matched expression by the regex module, `re`
            n_whitelines: Desired number of whitelines to use to replace all leading
            whitelines in `match`

        Returns:
            A string corresponding to the matched string with its leading whitelines
            replaced by `n_whitelines` whitelines.
        """
        matched_str = match.group()
        adjusted_matched_str = "\n" * (n_whitelines + 1) + matched_str.lstrip("\n")

        return adjusted_matched_str

    def _fix_section_whitelines(self, source_code: str) -> str:
        re_section = "\n*(^#.*\n)*\n*^[^ ].*:\n(\n|(^  .*))+\n*"

        # Match the first --- or start of the string \A
        # See: https://docs.python.org/3.9/library/re.html#regular-expression-syntax
        re_beginning_section = f"(?P<b>(?:---\n|\\A){re_section})"
        re_normal_section = f"(?P<s>{re_section})"
        re_full = f"{re_beginning_section}|{re_normal_section}"
        pattern = re.compile(re_full, flags=re.MULTILINE)
        n_whitelines = self.config.whitelines
        n_section_whitelines = self.config.section_whitelines

        def _fix_before_section(match: Match[str]) -> str:
            whitelines = n_section_whitelines
            section = match.group("s")
            if not section:
                return match.group()
            if n_whitelines > n_section_whitelines and section.startswith(
                "\n" + n_whitelines * "\n"
            ):
                whitelines = n_whitelines
            while section[0] == "\n":
                section = section[1:]
            return "\n" * (whitelines + 1) + section

        def _fix_after_section(match: Match[str]) -> str:
            whitelines = n_section_whitelines
            section = match.group("b") or match.group("s")
            if n_whitelines > n_section_whitelines and section.endswith(
                "\n\n" + n_whitelines * "\n"
            ):
                whitelines = n_whitelines
            while section[-1] == "\n":
                section = section[:-1]
            return section + "\n" * (whitelines + 1)

        before_fixed = pattern.sub(repl=_fix_before_section, string=source_code)
        after_fixed = pattern.sub(repl=_fix_after_section, string=before_fixed)
        while after_fixed[-2:] == "\n\n":
            after_fixed = after_fixed[:-1]
        return after_fixed

    @staticmethod
    def _restore_double_exclamations(source_code: str) -> str:
        """Restore the double exclamation marks.

        The Ruyaml parser transforms the !!python statement to !%21python which breaks
        some programs.
        """
        log.debug("Restoring double exclamations...")
        fixed_source_lines = []
        double_exclamation = re.compile(r"!%21")

        for line in source_code.splitlines():
            if double_exclamation.search(line):
                line = line.replace(r"!%21", "!!")
            fixed_source_lines.append(line)

        return "\n".join(fixed_source_lines)

    @staticmethod
    def _add_newline_at_end_of_file(source_code: str) -> str:
        """Ensures that the file ends with exactly one newline.

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        return source_code.rstrip() + "\n"

    @staticmethod
    def _fix_jinja_variables(source_code: str) -> str:
        """Remove spaces between jinja variables.

        So that they are not split in many lines by ruyaml

        Args:
            source_code: Source code to be corrected.

        Returns:
            Corrected source code.
        """
        log.debug("Fixing jinja2 variables...")
        source_lines = source_code.splitlines()
        fixed_source_lines: List[str] = []

        for line in source_lines:
            line_contains_jinja2_variable = re.search(r"{{.*}}", line)

            if line_contains_jinja2_variable:
                line = SourceCodeFixer._encode_jinja2_line(line)

            fixed_source_lines.append(line)

        return "\n".join(fixed_source_lines)

    @staticmethod
    def _encode_jinja2_line(line: str) -> str:
        """Encode jinja variables so that they are not split.

        Using a special character to join the elements inside the {{ }}, so that
        they are all taken as the same word, and ruyamel doesn't split them.
        """
        new_line = []
        variable_terms: List[str] = []

        for word in line.split(" "):
            if re.search("}}", word):
                variable_terms.append(word)
                new_line.append("★".join(variable_terms))
                variable_terms = []
            elif re.search("{{", word) or len(variable_terms) > 0:
                variable_terms.append(word)
            else:
                new_line.append(word)

        return " ".join(new_line)

    @staticmethod
    def _restore_jinja_variables(source_code: str) -> str:
        """Restore the jinja2 variables to their original state.

        Remove the encoding introduced by _fix_jinja_variables to prevent ruyaml
        to split the variables.
        """
        log.debug("Restoring jinja2 variables...")
        fixed_source_lines = []

        for line in source_code.splitlines():
            line_contains_jinja2_variable = re.search(r"{{.*}}", line)

            if line_contains_jinja2_variable:
                line = line.replace("★", " ")

            fixed_source_lines.append(line)

        return "\n".join(fixed_source_lines)
