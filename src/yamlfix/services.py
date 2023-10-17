"""Define all the orchestration functionality required by the program to work.

Classes and functions that connect the different domain model objects with the adapters
and handlers to achieve the program's purpose.
"""

import logging
import warnings
from typing import List, Optional, Tuple, Union, overload

from _io import TextIOWrapper

from yamlfix.adapters import SourceCodeFixer, Yaml
from yamlfix.model import YamlfixConfig

log = logging.getLogger(__name__)

Files = Union[Tuple[TextIOWrapper], List[str]]


@overload
def fix_files(files: Files) -> Optional[str]:
    ...  # pragma: no cover


@overload
def fix_files(files: Files, dry_run: Optional[bool]) -> Tuple[Optional[str], bool]:
    ...  # pragma: no cover


@overload
def fix_files(
    files: Files, dry_run: Optional[bool], config: Optional[YamlfixConfig]
) -> Tuple[Optional[str], bool]:
    ...  # pragma: no cover


def fix_files(  # pylint: disable=too-many-branches
    files: Files, dry_run: Optional[bool] = None, config: Optional[YamlfixConfig] = None
) -> Union[Optional[str], Tuple[Optional[str], bool]]:  # noqa: TAE002
    """Fix the yaml source code of a list of files.

    If the input is taken from stdin, it will return the fixed value.

    Args:
        files: List of files to fix.
        dry_run: Whether to write changes or not.
        config: Small set of user provided configuration options for yamlfix.

    Returns:
        A tuple with the following items:
        * Fixed code or None.
        * A bool to indicate whether at least one file has been changed.
    """
    changed = False

    if dry_run is None:
        warnings.warn(
            """
            From 2023-01-12 fix_files will change the return type from
            `Optional[str]` to Tuple[Optional[str], bool], where the first
            element of the Tuple is the fixed source and the second a bool that
            returns whether the source has changed.

            For more information check https://github.com/lyz-code/yamlfix/pull/182
            """,
            UserWarning,
            stacklevel=2,
        )

    total_fixed = 0

    for file_ in files:
        if isinstance(file_, str):
            with open(file_, "r", encoding="utf-8") as file_descriptor:
                source = file_descriptor.read()
                file_name = file_
        else:
            source = file_.read()
            file_name = file_.name

        log.debug("Fixing file %s...", file_name)
        fixed_source = fix_code(source, config)

        if fixed_source != source:
            changed = True
            if dry_run:
                log.info("Would fix %s", file_name)
            else:
                log.info("Fixed %s", file_name)
                total_fixed += 1
        else:
            log.log(15, "%s is already well formatted", file_name)

        if file_name == "<stdin>":
            if dry_run is None:
                return fixed_source
            return fixed_source, changed

        if fixed_source != source:
            if dry_run:
                continue
            if isinstance(file_, str):
                with open(file_, "w", encoding="utf-8") as file_descriptor:
                    file_descriptor.write(fixed_source)
            else:
                file_.seek(0)
                file_.write(fixed_source)
                file_.truncate()
    log.info(
        "Checked %d files: %d fixed, %d left unchanged",
        len(files),
        total_fixed,
        len(files) - total_fixed,
    )

    if dry_run is None:
        return None

    return None, changed


def fix_code(source_code: str, config: Optional[YamlfixConfig] = None) -> str:
    """Fix yaml source code to correct the format.

    It corrects these errors:

        * Add --- at the beginning of the file.
        * Correct truthy strings: 'True' -> true, 'no' -> 'false'
        * Remove unnecessary apostrophes: `title: 'Why we sleep'` ->
            `title: Why we sleep`.

    Args:
        source_code: Source code to be corrected.
        config: Small set of user provided configuration options for yamlfix.

    Returns:
        Corrected source code.
    """
    # Leave Ansible vaults unmodified
    if source_code.startswith("$ANSIBLE_VAULT;"):
        return source_code

    if source_code.startswith("#!"):
        # Skip the shebang line if present, leaving it unmodified
        eolpos = source_code.find("\n") + 1
        shebang = source_code[:eolpos]
        source_code = source_code[eolpos:]
    else:
        shebang = ""

    if source_code.startswith("#jinja2:") or source_code.startswith("# jinja2:"):
        eolpos = source_code.find("\n") + 1
        jinja2 = source_code[:eolpos]
        source_code = source_code[eolpos:]
    else:
        jinja2 = ""

    yaml = Yaml(config=config)
    fixer = SourceCodeFixer(yaml=yaml, config=config)

    source_code = fixer.fix(source_code=source_code)

    return jinja2 + shebang + source_code
