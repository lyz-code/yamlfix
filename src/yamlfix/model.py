"""Define program entities like configuration value entities."""
from enum import Enum
from typing import Optional

from maison.schema import ConfigSchema


class YamlNodeStyle(Enum):
    """Represent the desired YAML node style for sequences and mappings."""

    FLOW_STYLE = 1
    BLOCK_STYLE = 2
    KEEP_STYLE = 3


class YamlfixConfig(ConfigSchema):
    """Configuration entity for yamlfix."""

    allow_duplicate_keys: bool = False
    comments_min_spaces_from_content: int = 2
    comments_require_starting_space: bool = True
    config_path: Optional[str] = None
    explicit_start: bool = True
    style_sequence: YamlNodeStyle = YamlNodeStyle.FLOW_STYLE
    indent_mapping: int = 2
    indent_offset: int = 2
    indent_sequence: int = 4
    line_length: int = 80
    none_representation: str = ""
    quote_basic_values: bool = False
    quote_keys_and_basic_values: bool = False
    quote_representation: str = "'"
