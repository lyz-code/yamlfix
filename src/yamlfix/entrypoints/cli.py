"""Command line interface definition."""
import logging
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
@click.argument("files", type=click.File("r+"), required=True, nargs=-1)
def cli(files: Tuple[str], verbose: bool) -> None:
    """Corrects the source code of the specified files."""
    load_logger(verbose)
    log.info("Fixing files:%s", _format_file_list(files))
    fixed_code = services.fix_files(files)

    if fixed_code is not None:
        print(fixed_code, end="")
    log.info("Done.")


if __name__ == "__main__":  # pragma: no cover
    cli()  # pylint: disable=E1120
