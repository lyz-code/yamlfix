"""Define all the orchestration functionality required by the program to work.

Classes and functions that connect the different domain model objects with the adapters
and handlers to achieve the program's purpose.
"""

import logging
import re
import warnings
from io import StringIO
from typing import List, Optional, Tuple, Union, overload

import ruyaml
from _io import TextIOWrapper

log = logging.getLogger(__name__)

Files = Union[Tuple[TextIOWrapper], List[str]]


@overload
def fix_files(files: Files) -> Optional[str]:
    ...


@overload
def fix_files(files: Files, dry_run: Optional[bool]) -> Tuple[Optional[str], bool]:
    ...


def fix_files(  # pylint: disable=too-many-branches
    files: Files, dry_run: Optional[bool] = None
) -> Union[Optional[str], Tuple[Optional[str], bool]]:  # noqa: TAE002
    """Fix the yaml source code of a list of files.

    If the input is taken from stdin, it will return the fixed value.

    Args:
        files: List of files to fix.
        dry_run: Whether to write changes or not.

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
        )

    for file_ in files:
        if isinstance(file_, str):
            with open(file_, "r", encoding="utf-8") as file_descriptor:
                source = file_descriptor.read()
                file_name = file_
        else:
            source = file_.read()
            file_name = file_.name

        log.debug("Fixing file %s...", file_name)
        fixed_source = fix_code(source)

        if fixed_source != source:
            changed = True

        if file_name == "<stdin>":
            if dry_run is None:
                return fixed_source
            return (fixed_source, changed)

        if fixed_source != source:
            if dry_run:
                log.debug("Need to fix file %s.", file_name)
                continue
            if isinstance(file_, str):
                with open(file_, "w", encoding="utf-8") as file_descriptor:
                    file_descriptor.write(fixed_source)
            else:
                file_.seek(0)
                file_.write(fixed_source)
                file_.truncate()
            log.debug("Fixed file %s.", file_name)
        else:
            log.debug("Left file %s unmodified.", file_name)

    if dry_run is None:
        return None

    return (None, changed)


def fix_code(source_code: str) -> str:
    """Fix yaml source code to correct the format.

    It corrects these errors:

        * Add --- at the beginning of the file.
        * Correct truthy strings: 'True' -> true, 'no' -> 'false'
        * Remove unnecessary apostrophes: `title: 'Why we sleep'` ->
            `title: Why we sleep`.

    Args:
        source_code: Source code to be corrected.

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

    fixers = [
        _fix_truthy_strings,
        _fix_comments,
        _fix_jinja_variables,
        _ruamel_yaml_fixer,
        _restore_truthy_strings,
        _restore_double_exclamations,
        _restore_jinja_variables,
        _fix_top_level_lists,
        _add_newline_at_end_of_file,
    ]
    for fixer in fixers:
        source_code = fixer(source_code)

    return shebang + source_code


def _ruamel_yaml_fixer(source_code: str) -> str:
    """Run Ruamel's yaml fixer.

    Args:
        source_code: Source code to be corrected.

    Returns:
        Corrected source code.
    """
    log.debug("Running ruamel yaml fixer...")
    # Configure YAML formatter
    yaml = ruyaml.main.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.allow_duplicate_keys = True
    # Start the document with ---
    # ignore: variable has type None, what can we do, it doesn't have type hints...
    yaml.explicit_start = True  # type: ignore
    yaml.width = 80  # type: ignore
    source_dicts = yaml.load_all(source_code)

    # Return the output to a string
    string_stream = StringIO()
    for source_dict in source_dicts:
        yaml.dump(source_dict, string_stream)
        source_code = string_stream.getvalue()
    string_stream.close()

    return source_code.strip()


def _fix_top_level_lists(source_code: str) -> str:
    """Deindent the source with a top level list.

    Documents like the following:

    ```yaml
    ---
    # Comment
    - item 1
    - item 2
    ```

    Are wrongly indented by the ruyaml parser:

    ```yaml
    ---
    # Comment
      - item 1
      - item 2
    ```

    This function restores the indentation back to the original.

    Args:
        source_code: Source code to be corrected.

    Returns:
        Corrected source code.
    """
    log.debug("Fixing top level lists...")
    source_lines = source_code.splitlines()
    fixed_source_lines: List[str] = []
    is_top_level_list: Optional[bool] = None

    for line in source_lines:

        # Skip the heading and first empty lines
        if re.match(r"^(---|#.*|)$", line):
            fixed_source_lines.append(line)
            continue

        # Check if the first valid line is an indented list item
        if re.match(r"\s*- +.*", line) and is_top_level_list is None:
            is_top_level_list = True

            # Extract the indentation level
            serialized_line = re.match(r"(?P<indent>\s*)- +(?P<content>.*)", line)
            if serialized_line is None:  # pragma: no cover
                raise ValueError(f"Error extracting the indentation of line: {line}")
            indent = serialized_line.groupdict()["indent"]

            # Remove the indentation from the line
            fixed_source_lines.append(re.sub(rf"^{indent}(.*)", r"\1", line))
        elif is_top_level_list:
            fixed_source_lines.append(re.sub(rf"^{indent}(.*)", r"\1", line))
        else:
            return source_code

    return "\n".join(fixed_source_lines)


def _fix_truthy_strings(source_code: str) -> str:
    """Convert common strings that refer to booleans.

    All caps variations of true, yes and on are transformed to true, while false, no and
    off are transformed to false.

    Ruyaml understands these strings and converts them to the lower version of the word
    instead of converting them to true and false.

    [More
    info](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy)

    Args:
        source_code: Source code to be corrected.

    Returns:
        Corrected source code.
    """
    log.debug("Fixing truthy strings...")
    source_lines = source_code.splitlines()
    fixed_source_lines: List[str] = []

    for line in source_lines:
        line_contains_true = re.match(
            r"(?P<pre_boolean_text>.*(:|-) )(true|yes|on)$", line, re.IGNORECASE
        )
        line_contains_false = re.match(
            r"(?P<pre_boolean_text>.*(:|-) )(false|no|off)$", line, re.IGNORECASE
        )

        if line_contains_true:
            fixed_source_lines.append(
                f"{line_contains_true.groupdict()['pre_boolean_text']}true"
            )
        elif line_contains_false:
            fixed_source_lines.append(
                f"{line_contains_false.groupdict()['pre_boolean_text']}false"
            )
        else:
            fixed_source_lines.append(line)

    return "\n".join(fixed_source_lines)


def _restore_truthy_strings(source_code: str) -> str:
    """Restore truthy strings to strings.

    The Ruyaml parser removes the apostrophes of all the caps variations of the strings
    'yes', 'on', no and 'off' as it interprets them as booleans.

    As this function is run after _fix_truthy_strings, those strings are meant to be
    strings. So we're turning them back from booleans to strings.

    Args:
        source_code: Source code to be corrected.

    Returns:
        Corrected source code.
    """
    log.debug("Restoring truthy strings...")
    source_lines = source_code.splitlines()
    fixed_source_lines: List[str] = []

    for line in source_lines:
        line_contains_valid_truthy_string = re.match(
            r"(?P<pre_boolean_text>.*(:|-) )(?P<boolean_text>yes|on|no|off)$",
            line,
            re.IGNORECASE,
        )
        if line_contains_valid_truthy_string:
            fixed_source_lines.append(
                f"{line_contains_valid_truthy_string.groupdict()['pre_boolean_text']}"
                f"'{line_contains_valid_truthy_string.groupdict()['boolean_text']}'"
            )
        else:
            fixed_source_lines.append(line)

    return "\n".join(fixed_source_lines)


def _fix_comments(source_code: str) -> str:
    log.debug("Fixing comments...")
    fixed_source_lines = []

    for line in source_code.splitlines():
        # Comment at the start of the line
        if re.search(r"(^|\s)#\w", line):
            line = line.replace("#", "# ")
        # Comment in the middle of the line, but it's not part of a string
        if re.match(r".+\S\s#", line) and line[-1] not in ["'", '"']:
            line = line.replace(" #", "  #")
        fixed_source_lines.append(line)

    return "\n".join(fixed_source_lines)


def _restore_double_exclamations(source_code: str) -> str:
    """Restore the double exclamation marks.

    The Ruyaml parser transforms the !!python statement to !%21python which breaks
    some programs.
    """
    log.debug("Restoring double exclamations...")
    fixed_source_lines = []
    double_exclamation = re.compile(r"!%21")

    for line in source_code.splitlines():
        if double_exclamation.search(line):
            line = line.replace(r"!%21", "!!")
        fixed_source_lines.append(line)

    return "\n".join(fixed_source_lines)


def _add_newline_at_end_of_file(source_code: str) -> str:
    return source_code + "\n"


def _fix_jinja_variables(source_code: str) -> str:
    """Remove spaces between jinja variables.

    So that they are not split in many lines by ruyaml

    Args:
        source_code: Source code to be corrected.

    Returns:
        Corrected source code.
    """
    log.debug("Fixing jinja2 variables...")
    source_lines = source_code.splitlines()
    fixed_source_lines: List[str] = []

    for line in source_lines:
        line_contains_jinja2_variable = re.search(r"{{.*}}", line)

        if line_contains_jinja2_variable:
            line = _encode_jinja2_line(line)

        fixed_source_lines.append(line)

    return "\n".join(fixed_source_lines)


def _encode_jinja2_line(line: str) -> str:
    """Encode jinja variables so that they are not split.

    Using a special character to join the elements inside the {{ }}, so that they are
    all taken as the same word, and ruyamel doesn't split them.
    """
    new_line = []
    variable_terms: List[str] = []

    for word in line.split(" "):
        if re.search("}}", word):
            variable_terms.append(word)
            new_line.append("★".join(variable_terms))
            variable_terms = []
        elif re.search("{{", word) or len(variable_terms) > 0:
            variable_terms.append(word)
        else:
            new_line.append(word)

    return " ".join(new_line)


def _restore_jinja_variables(source_code: str) -> str:
    """Restore the jinja2 variables to their original state.

    Remove the encoding introduced by _fix_jinja_variables to prevent ruyaml to split
    the variables.
    """
    log.debug("Restoring jinja2 variables...")
    fixed_source_lines = []

    for line in source_code.splitlines():
        line_contains_jinja2_variable = re.search(r"{{.*}}", line)

        if line_contains_jinja2_variable:
            line = line.replace("★", " ")

        fixed_source_lines.append(line)

    return "\n".join(fixed_source_lines)
