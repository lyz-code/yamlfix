"""Command line interface definition."""

import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

import click
from _io import TextIOWrapper

from yamlfix import services, version
from yamlfix.config import configure_yamlfix
from yamlfix.entrypoints import load_logger
from yamlfix.model import YamlfixConfig

log = logging.getLogger(__name__)


def _format_file_list(files: Tuple[TextIOWrapper]) -> str:
    file_names = [file.name for file in files]
    return "\n  - ".join([""] + file_names)


@click.command()
@click.version_option(version="", message=version.version_info())
@click.option("--verbose", is_flag=True, help="Enable verbose logging.")
@click.option(
    "--check",
    is_flag=True,
    help="Check if file(s) needs fixing. No files will be written in this case.",
)
@click.option(
    "--config-file",
    "-c",
    multiple=True,
    type=str,
    help="Path to a custom configuration file.",
)
@click.option(
    "--env-prefix",
    type=str,
    default="YAMLFIX",
    help="Read yamlfix relevant environment variables starting with this prefix.",
)
@click.argument("files", type=click.File("r+"), required=True, nargs=-1)
def cli(
    files: Tuple[str],
    verbose: bool,
    check: bool,
    config_file: Optional[List[str]],
    env_prefix: str,
) -> None:
    """Corrects the source code of the specified files."""
    load_logger(verbose)
    log.info("%s files:%s", "Checking" if check else "Fixing", _format_file_list(files))

    config = YamlfixConfig()
    configure_yamlfix(
        config, config_file, _parse_env_vars_as_yamlfix_config(env_prefix.lower())
    )

    fixed_code, changed = services.fix_files(files, check, config)

    if fixed_code is not None:
        print(fixed_code, end="")
    log.info("Done.")

    if changed and check:
        sys.exit(1)


def _parse_env_vars_as_yamlfix_config(env_prefix: str) -> Dict[str, str]:
    prefix_length = len(env_prefix) + 1  # prefix with underscore / delimiter (+1)
    additional_config: Dict[str, str] = {}

    for env_key, env_val in os.environ.items():
        sanitized_key = env_key.lower()

        if sanitized_key.startswith(env_prefix) and len(sanitized_key) > prefix_length:
            additional_config[sanitized_key[prefix_length:]] = env_val

    return additional_config


if __name__ == "__main__":  # pragma: no cover
    cli()  # pylint: disable=E1120
