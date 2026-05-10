# [DevBounty AI]: File optimized for resolution.


```python
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
            self.handle_comments,
        ]

        for patch_configurer in configure_patch_functions:
            patch_configurer()

    def handle_comments(self, node: Node, parent: Node) -> None:
        """Handle comments by preserving them."""
        if isinstance(node, CommentToken):
            # Preserve the comment by not modifying it
            pass

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
                    # Apply patch functions
                    for patch_function in self.patch_functions:
                        patch_function(mapping_value[1], mapping_node)
        return mapping_node