## 1.16.0 (2023-11-23)

### Feat

- support Python 3.11

### Fix

- drop support for Python 3.7
- switch from pdm-pep517 to pdm-backend

## 1.15.0 (2023-10-17)

## 1.14.0 (2023-08-31)

## 1.13.0 (2023-08-01)

## 1.12.0 (2023-07-02)

## 1.11.0 (2023-06-14)

### Feat

- add include and exclude cli options

## 1.10.0 (2023-05-26)

## 1.9.0 (2023-02-17)

## 1.8.1 (2023-02-13)

### Fix

- account for explicit_start=False when handline whitelines

## 1.8.0 (2023-02-06)

### Feat

- **services.py**: Change behaviour to only list changed files by default

### Fix

- **services.py**: Fix counting of fixed files
- **entrypoints.py/__init__.py**: Fix type

### Refactor

- **entrypoints/__init__.py**: Add comment about third logging level
- **entrypoints/__init__.py**: Move color codes back into their own list

## 1.7.0 (2023-01-31)

### Feat

- **cli.py**: Add ability to glob on directories

### Refactor

- **cli.py**: Use build-in required flag in click

## 1.6.0 (2023-01-26)

### Feat

- **adapters.py**: Add section whitelines

### Fix

- **adapters.py**: Fix behavior for section whitelines at the end of the document

## 1.5.0 (2023-01-16)

## 1.4.0 (2023-01-13)

## 1.3.1 (2023-01-02)

### Fix

- compare sequence_style with proper (enum) type and add more tests

## 1.3.0 (2022-12-27)

### Feat

- make space after comment start and spaces before inline-comment configurable

### Fix

- comment fix was only applied to yaml source before ruyaml ran, not after, which missed some comment fixes after block/flow style conversions
- issues with flow-style inline-comments

## 1.2.0 (2022-12-20)

### Feat

- add use-case / check workaround for issue #188
- add quotations to simple list values as well
- make yamlfix configurable with sane default values

### Fix

- correct wrong wording in 'allow_duplicate_keys' docs and set default value to 'False'
- apply pull request suggestions by setting default values, and removing flow-style multi-line support
- update pre-commit hook versions, align mypy config with pyproject.toml, remove flakehell and add flakeheaven

## 1.1.1 (2022-11-25)

### Fix

- remove dependency with py
- restore the comment identation management

## 1.1.0 (2022-09-14)

## 1.0.1 (2022-08-01)

### Fix

- don't erase strings that are a jinja2 variable expansion

## 1.0.0 (2022-08-01)

### Feat

- stabilize the package

## 0.10.1 (2022-08-01)

### Fix

- don't break jinja2 expansion on variables assignment

## 0.10.0 (2022-07-11)

### Feat

- add support to jinja2 variables
- add support to line cropping

## 0.9.0 (2022-03-11)

### Fix

- allow fix_files to read paths to files as arguments
- allow fix_files to read paths to files as arguments

### Feat

- use pdm as package manager
- use pdm as package manager

## 0.8.2 (2022-03-07)

## 0.8.1 (2022-02-21)

### Fix

- fix types of pre-commit-hooks

## 0.8.0 (2021-12-01)

### Feat

- don't overwrite files if content is not modified. Closes #142.

## 0.7.6 (2021-11-30)

### Fix

- support comments in the middle of a string

## 0.7.5 (2021-11-29)

### Fix

- Moved shebang skipping code to fix_code instead of fix_files. Closes #123

## 0.7.4 (2021-11-26)

### Fix

- revert the ruyaml dependency
- don't modify Ansible vaults. Closes #135.
- make docstring match functionality, closes #133

## 0.7.3 (2021-09-22)

### Fix

- update ruyaml version with anchor bug fix

## 0.7.2 (2021-09-02)

### Fix

- add newline at end of file

## 0.7.1 (2021-08-24)

### Fix

- remove leftover warning log

## 0.7.0 (2021-08-23)

### Fix

- remove workaround for stdin tests
- turn 'files' into required arg
- add logging formatter and preserve levels

### Feat

- add logs and logging tests

## 0.6.0 (2021-08-21)

### Feat

- allow formatting files with multiple documents

## 0.5.0 (2021-04-23)

### Fix

- install wheel in the build pipeline

### feat

- add a ci job to test that the program is installable

## 0.4.2 (2021-04-23)

### Fix

- replace ruamel.yaml with ruyaml

### fix

- respect the double exclamation marks in the variables

## 0.4.1 (2021-03-18)

### Fix

- respect anchors in urls

## 0.4.0 (2021-02-05)

### Feat

- allow the use of yamlfix as a pre-commit hook

### Fix

- respect comments indentation in lists.

## 0.3.0 (2020-12-10)

### Feat

- manage comments

## 0.2.1 (2020-11-30)

### Fix

- correct indentation of parent lists with comments

## 0.2.0 (2020-11-26)

### Feat

- correct truthy strings (#3)

### Fix

- correct indentation of top level lists (#5)

### refactor

- remove _add_heading in favour of explicit_start attribute

## 0.1.0 (2020-11-25)

### Feat

- initial iteration
- create initial project structure
