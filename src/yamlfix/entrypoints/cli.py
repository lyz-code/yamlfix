"""Command line interface definition."""

from typing import Tuple

import click

from yamlfix import services, version


@click.command()
@click.version_option(version="", message=version.version_info())
@click.argument("files", type=click.File("r+"), nargs=-1)
def cli(files: Tuple[str]) -> None:
    """Corrects the source code of the specified files."""
    fixed_code = services.fix_files(files)

    if fixed_code is not None:
        print(fixed_code, end="")


if __name__ == "__main__":  # pragma: no cover
    cli()  # pylint: disable=E1120
