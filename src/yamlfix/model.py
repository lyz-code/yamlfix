"""Define program entities like configuration value entities."""

from typing import Optional

from maison.schema import ConfigSchema


class YamlfixConfig(ConfigSchema):
    """Configuration entity for yamlfix."""

    allow_duplicate_keys: bool = False
    config_path: Optional[str] = None
    explicit_start: bool = True
    flow_style_sequence: Optional[bool] = True
    indent_mapping: int = 2
    indent_offset: int = 2
    indent_sequence: int = 4
    line_length: int = 80
    none_representation: str = ""
    quote_basic_values: bool = False
    quote_keys_and_basic_values: bool = False
    quote_representation: str = "'"
