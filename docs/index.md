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

    ```python
    from yamlfix import fix_files

    fix_files(['file.py'])
    ```

# Features

yamlfix will do the following changes in your code:

* Add the header `---` to your file.
* [Correct truthy
    strings](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy):
    'True' -> true, 'no' -> 'false'
* Remove unnecessary apostrophes: `title: 'Why we sleep'` -> `title: Why we sleep`.
* [Correct comments](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.comments)

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

# Contributing

For guidance on setting up a development environment, and how to make
a contribution to *yamlfix*, see [Contributing to
yamlfix](https://lyz-code.github.io/yamlfix/contributing).
