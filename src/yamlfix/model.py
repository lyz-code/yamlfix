"""Define program entities like configuration value entities."""
from enum import Enum
from typing import Optional

from maison.schema import ConfigSchema


class YamlNodeStyle(Enum):
    """Represent the desired YAML node style for sequences and mappings."""

    FLOW_STYLE = "flow_style"
    BLOCK_STYLE = "block_style"
    KEEP_STYLE = "keep_style"


class YamlfixConfig(ConfigSchema):
    """Configuration entity for yamlfix."""

    allow_duplicate_keys: bool = False
    comments_min_spaces_from_content: int = 2
    comments_require_starting_space: bool = True
    comments_whitelines: int = 1
    whitelines: int = 0
    section_whitelines: int = 0
    config_path: Optional[str] = None
    explicit_start: bool = True
    indent_mapping: int = 2
    indent_offset: int = 2
    indent_sequence: int = 4
    line_length: int = 80
    none_representation: str = ""
    quote_basic_values: bool = False
    quote_keys_and_basic_values: bool = False
    preserve_quotes: bool = False
    quote_representation: str = "'"
    sequence_style: YamlNodeStyle = YamlNodeStyle.FLOW_STYLE
