"""Command line interface definition."""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click

from yamlfix import services, version
from yamlfix.config import configure_yamlfix
from yamlfix.entrypoints import load_logger
from yamlfix.model import YamlfixConfig
from yamlfix.services import Files

log = logging.getLogger(__name__)


def _find_all_yaml_files(
    dir_: Path, include_globs: List[str], exclude_globs: Optional[List[str]]
) -> List[Path]:
    files = {f for glob in (include_globs) for f in dir_.rglob(glob) if f.is_file()}
    files.difference_update(f for exc in (exclude_globs or []) for f in dir_.rglob(exc))
    return sorted(files)


@click.command()
@click.version_option(version="", message=version.version_info())
@click.option("--verbose", "-v", help="Enable verbose logging.", count=True)
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
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    type=str,
    help="Files matching this glob pattern will be ignored.",
)
@click.option(
    "--include",
    "-i",
    multiple=True,
    type=str,
    default=["*.yaml", "*.yml"],
    help=(
        "Files matching this glob pattern will be included, "
        "unless they are also excluded. Default to '*.yaml' and '*.yml'."
    ),
)
@click.argument("files", type=str, required=True, nargs=-1)
def cli(  # pylint: disable=too-many-arguments
    files: Tuple[str],
    verbose: bool,
    check: bool,
    config_file: Optional[List[str]],
    include: List[str],
    exclude: Optional[List[str]],
    env_prefix: str,
) -> None:
    """Corrects the source code of the specified files.

    Specify directory to recursively fix all yaml files in it.

    Use - to read from stdin. No other files can be specified in this case.
    """
    files_to_fix: Files = []
    if "-" in files:
        if len(files) > 1:
            raise ValueError("Cannot specify '-' and other files at the same time.")
        files_to_fix = (sys.stdin,)  # type: ignore[assignment]
    else:
        paths = [Path(file) for file in files]
        real_files = []
        for provided_file in paths:
            if provided_file.is_dir():
                real_files.extend(_find_all_yaml_files(provided_file, include, exclude))
            else:
                real_files.append(provided_file)
        files_to_fix = [str(file) for file in real_files]
    if not files_to_fix:
        log.warning("No YAML files found!")
        sys.exit(0)

    load_logger(verbose)
    log.info("YamlFix: %s files", "Checking" if check else "Fixing")

    config = YamlfixConfig()
    configure_yamlfix(
        config, config_file, _parse_env_vars_as_yamlfix_config(env_prefix.lower())
    )

    fixed_code, changed = services.fix_files(files_to_fix, check, config)

    if fixed_code is not None:
        print(fixed_code, end="")

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
