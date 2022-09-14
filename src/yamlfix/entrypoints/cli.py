"""Command line interface definition."""

import logging
import sys
from typing import Tuple

import click
from _io import TextIOWrapper

from yamlfix import services, version
from yamlfix.entrypoints import load_logger

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
@click.argument("files", type=click.File("r+"), required=True, nargs=-1)
def cli(files: Tuple[str], verbose: bool, check: bool) -> None:
    """Corrects the source code of the specified files."""
    load_logger(verbose)
    log.info("%s files:%s", "Checking" if check else "Fixing", _format_file_list(files))

    fixed_code, changed = services.fix_files(files, check)

    if fixed_code is not None:
        print(fixed_code, end="")
    log.info("Done.")

    if changed and check:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    cli()  # pylint: disable=E1120
