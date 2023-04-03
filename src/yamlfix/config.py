"""Define the configuration of the main program."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from maison.config import ProjectConfig

from yamlfix.model import YamlfixConfig


def configure_yamlfix(
    yamlfix_config: YamlfixConfig,
    config_files: Optional[List[str]] = None,
    additional_config: Optional[Dict[str, str]] = None,
) -> None:
    """Configure the YamlfixConfig object from .toml/.ini configuration files \
        and additional config overrides."""
    config_path: Optional[Path] = None

    if additional_config:
        config_path_env: Optional[str] = additional_config.get("config_path")
        if config_path_env:
            config_path = Path(config_path_env)

    config: ProjectConfig = ProjectConfig(
        config_schema=YamlfixConfig,
        merge_configs=True,
        project_name="yamlfix",
        source_files=config_files,
        starting_path=config_path,
    )
    config_dict: Dict[str, Any] = config.to_dict()

    if additional_config:
        for override_key, override_val in additional_config.items():
            config_dict[override_key] = override_val

    config.validate()
    config_dict = config.to_dict()

    for config_key, config_val in config_dict.items():
        setattr(yamlfix_config, config_key, config_val)
