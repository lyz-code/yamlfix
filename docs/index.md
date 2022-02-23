[![Actions Status](https://github.com/lyz-code/yamlfix/workflows/Tests/badge.svg)](https://github.com/lyz-code/yamlfix/actions)
[![Actions Status](https://github.com/lyz-code/yamlfix/workflows/Build/badge.svg)](https://github.com/lyz-code/yamlfix/actions)
[![Coverage Status](https://coveralls.io/repos/github/lyz-code/yamlfix/badge.svg?branch=master)](https://coveralls.io/github/lyz-code/yamlfix?branch=master)

A simple opinionated yaml formatter that keeps your comments!

# Installing

```bash
pip install yamlfix
```

# Usage

Imagine we've got the following source code:

```yaml
book_library:
- title: Why we sleep
  author: Matthew Walker
- title: Harry Potter and the Methods of Rationality
  author: Eliezer Yudkowsky
```

It has the following errors:

* There is no `---` at the top.
* The indentation is all wrong.

After running `yamlfix` the resulting source code will be:

```yaml
---
book_library:
  - title: Why we sleep
    author: Matthew Walker
  - title: Harry Potter and the Methods of Rationality
    author: Eliezer Yudkowsky
```

`yamlfix` can be used both as command line tool and as a library.

* As a command line tool:

    ```bash
    $: yamlfix file.yaml
    ```

* As a library:

  For multiple files

    ```python
    from yamlfix import fix_files

    fix_files(['file.py'])
    ```
  where `'[file.py]`can be replaced by using the following expression:
    ```python
    file_a = TextIOWrapper(open('fileA.yml', 'r+b'))
    file_b = TextIOWrapper(open('fileB.yml', 'r+b'))
    wrapper_tuple = file_a, file_b
    fix_files(wrapper_tuple)
    ```
  For a single file using
     ```python
     from yamlfix import fix_code
     file_a = 'fileA.yml'
     yamlfix.fix_code(file_a)
     ```

# Features

yamlfix will do the following changes in your code:

* Add the header `---` to your file.
* [Correct truthy
    strings](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy):
    'True' -> true, 'no' -> 'false'
* Remove unnecessary apostrophes: `title: 'Why we sleep'` -> `title: Why we sleep`.
* [Correct comments](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.comments)
* Ensure that there is exactly one newline at the end of each file, to comply with the [POSIX standard](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap03.html#tag_03_206).

# References

As most open sourced programs, `yamlfix` is standing on the shoulders of
giants, namely:

[yamlfmt](https://github.com/mmlb/yamlfmt)
: Inspiration and alternative of this program. I created a new one because the
    pace of their pull requests is really slow, they don't have tests, CI pipelines
    or documentation.

[ruyaml](https://github.com/pycontribs/ruyaml)
: A git based community maintained for of
[ruamel](https://yaml.readthedocs.io/en/latest/) yaml parser.

[Click](https://click.palletsprojects.com/)
: Used to create the command line interface.

[Pytest](https://docs.pytest.org/en/latest)
: Testing framework, enhanced by the awesome
    [pytest-cases](https://smarie.github.io/python-pytest-cases/) library that made
    the parametrization of the tests a lovely experience.

[Mypy](https://mypy.readthedocs.io/en/stable/)
: Python static type checker.

[Flakehell](https://github.com/life4/flakehell)
: Python linter with [lots of
    checks](https://lyz-code.github.io/blue-book/devops/flakehell/#plugins).

[Black](https://black.readthedocs.io/en/stable/)
: Python formatter to keep a nice style without effort.

[Autoimport](https://github.com/lyz-code/autoimport)
: Python formatter to automatically fix wrong import statements.

[isort](https://github.com/timothycrosley/isort)
: Python formatter to order the import statements.

[Pip-tools](https://github.com/jazzband/pip-tools)
: Command line tool to manage the dependencies.

[Mkdocs](https://www.mkdocs.org/)
: To build this documentation site, with the
[Material theme](https://squidfunk.github.io/mkdocs-material).

[Safety](https://github.com/pyupio/safety)
: To check the installed dependencies for known security vulnerabilities.

[Bandit](https://bandit.readthedocs.io/en/latest/)
: To finds common security issues in Python code.

# Contributing

For guidance on setting up a development environment, and how to make
a contribution to *yamlfix*, see [Contributing to
yamlfix](https://lyz-code.github.io/yamlfix/contributing).
