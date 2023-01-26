[![Actions Status](https://github.com/lyz-code/yamlfix/workflows/Tests/badge.svg)](https://github.com/lyz-code/yamlfix/actions)
[![Actions Status](https://github.com/lyz-code/yamlfix/workflows/Build/badge.svg)](https://github.com/lyz-code/yamlfix/actions)
[![Coverage Status](https://coveralls.io/repos/github/lyz-code/yamlfix/badge.svg?branch=main)](https://coveralls.io/github/lyz-code/yamlfix?branch=main)

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

- There is no `---` at the top.
- The indentation is all wrong.

After running `yamlfix` the resulting source code will be:

```yaml
book_library:
  - title: Why we sleep
    author: Matthew Walker
  - title: Harry Potter and the Methods of Rationality
    author: Eliezer Yudkowsky
```

`yamlfix` can be used both as command line tool and as a library.

As a command line tool:

```bash
$: yamlfix file.yaml
```

As a library:

```python
from yamlfix import fix_files

fix_files(["file.py"])
```

If instead of reading from a file you want to fix the code saved into a
variable, use `fix_code`:

```python
{! examples/fix_code.py !}
```

# Features

`yamlfix` will do the following changes in your yaml source code per default:

- Add the header `---` to your file.
- [Correct truthy strings](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.truthy):
  'True' -> true, 'no' -> 'false'
- Remove unnecessary apostrophes: `title: 'Why we sleep'` ->
  `title: Why we sleep`.
- [Correct comments](https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.comments)
- Ensure that there is exactly one newline at the end of each file, to comply
  with the
  [POSIX standard](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap03.html#tag_03_206).
- Split long lines.
- Respect Jinja2 syntax.
- Ensure a `\n` exists at the end of the file.
- Convert short lists to flow-style `list: [item, item]`
- Convert lists longer than line-width to block-style:
  ```yaml
  list:
    - item
    - item
  ```

# Configuration

`yamlfix` uses the `maison` library to find and parse configuration from standard locations, and can additionally be configured through environment variables.

Any configuration found in the [YamlfixConfig class](./reference/#yamlfix.model.YamlfixConfig) can be set through your projects `pyproject.toml`, a custom `toml`-file or through the environment by providing an environment variable like `{yamlfix_env_prefix}_{yamlfix_config_key}`.

Configuration options that are provided through environment variables have higher priority than options provided through configuration files and will override those keys.

All provided [configuration options](#configuration-options), be it through `pyproject.toml`, config-files or env-vars, will be parsed by `pydantic`, so the target value type (str, bool, int, etc.) will be enforced, even if the provided value has the wrong type (for example all env vars in linux systems are strings, but pydantic will parse them to bools/numbers where necessary).

## Auto-Configure through `pyproject.toml`

The `maison` library will automatically pick up your `yamlfix` configuration through your projects `pyproject.toml`. It will look in the section named `tool.yamlfix` and apply the provided [configuration options](#configuration-options). For example:

```toml
# pyproject.toml

[tool.yamlfix]
allow_duplicate_keys = true
line_length = 80
none_representation = "null"
```

## Provide config-files

When running `yamlfix` as a standalone cli application it might be desireable to provide a config file containing just the configuration related to `yamlfix`. A cli-argument `-c` (`--config-file`) can be provided multiple times to read configuration values from `toml` formatted files. The rightmost value-files override the value-files preceding them, only trumped by environment variables. No section headers are necessary for these configuration files, as the expected behaviour is, that those files contain only configuration related to `yamlfix`. For example:

```bash
# run yamlfix with two config files
yamlfix -c base.toml --config-file environment.toml file.yaml
```

```toml
# base.toml
allow_duplicate_keys = false
line_length = 100
```

```toml
# environment.toml
allow_duplicate_keys = true
```

These provided configuration files would result in a merged runtime-configuration of:
```toml
# merged configuration
allow_duplicate_keys = true
line_length = 100
```

## Configure environment prefix

Per default `yamlfix`, when run through cli, will read any environment variable that starts with `YAMLFIX_` and apply it to the merged runtime-configuration object. This default value can be overridden with the cli-parameter `--env-prefix`. For example:

```bash
# set a configuration value with the default prefix
export YAMLFIX_LINE_LENGTH="300"

# set a configuration value with the custom prefix
export MY_PREFIX_NONE_REPRESENTATION="~"

# run yamlfix with a custom environment prefix
yamlfix --env-prefix "MY_PREFIX" file.yaml
```

These provided arguments and environment variables would result in a merged runtime-configuration of:
```toml
# merged configuration
# default value for line_length stays at: 80
none_representation = "~"
```

## Configuration Options

All fields configured in the [YamlfixConfig class](./reference/#yamlfix.model.YamlfixConfig) can be provided through the means mentioned in [Configuration](#configuration). Here are the currently available configuration options with short examples on their impact to provided `yaml`-files.

### Allow Duplicate Keys

Default: `allow_duplicate_keys: bool = False`<br>
Environment variable override:
```bash
export YAMLFIX_ALLOW_DUPLICATE_KEYS="true"
```

This option toggles the [ruyaml duplicate keys check](https://ruyaml.readthedocs.io/en/latest/api.html#duplicate-keys). With this setting set to `False`, `yamlfix` will throw an error if the same key is defined more than once in a mapping / dictionary. To allow using the same key, set this value to `True`. You might want to enable this option, if you want to use multiple yaml-anchor merge keys, instead of providing them as sequence / list elements - see: https://github.com/pycontribs/ruyaml/issues/43

### Comments Min Spaces From Content

Default: `comments_min_spaces_from_content: int = 2`<br>
Environment variable override:
```bash
export YAMLFIX_COMMENTS_MIN_SPACES_FROM_CONTENT="2"
```

This option enforces minimum spacing between the content of a line and the start of an inline-comment. It is the enforcement implementation to the yamllint rule `rules.comments.min-spaces-from-content` - see: https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.comments

### Comments Require Starting Space

Default: `comments_require_starting_space: bool = True`<br>
Environment variable override:
```bash
export YAMLFIX_COMMENTS_REQUIRE_STARTING_SPACE="true"
```

This option enforces a space between the comment indicator (`#`) and the first character in the comment. It implements the enforcement of the yamllint rule `rules.comments.require-starting-space` - see: https://yamllint.readthedocs.io/en/stable/rules.html#module-yamllint.rules.comments

### Comments Whitelines

Default: `comments_whitelines: int = 1`<br>
Environment variable override:
```bash
export YAMLFIX_COMMENTS_WHITELINES="1"
```

This option allows to add a specific number of consecutive whitelines before a comment-only line.

A comment-only line is defined as a line that starts with a comment or with an indented comment.

Before a comment-only line, either:

- 0 whiteline is allowed
- Exactly `comments_whitelines` whitelines are allowed

### Section Whitelines
Default `section_whitelines: int = 0`<br>
Environment variable override:
```bash
export YAMLFIX_SECTION_WHITELINES="1"
```

This option sets the number of whitelines before and after a section.
A section is defined as a top-level key followed by at least one line with indentation.
Section examples:
```yaml
section1:
  key: value

list:
  - value
```
There are a few exceptions to this behaviour:

* If there is a comment(s) on the line(s) preceding beginning of a section, `comments_whitelines` rules will be applied to whitelines before the section. e.g.
```yaml
# Comment
section:
  key: value
```
* Sections at the start and end of the document will have whitelines removed before and after respectively.


### Config Path

Default: `config_path: Optional[str] = None`<br>
Environment variable override:
```bash
export YAMLFIX_CONFIG_PATH="/etc/yamlfix/"
```

Configure the base config-path that `maison` will look for a `pyproject.toml` configuration file. This path is traversed upwards until such a file is found.

### Explicit Document Start

Default: `explicit_start: bool = True`<br>
Environment variable override:
```bash
export YAMLFIX_EXPLICIT_START="true"
```

Add or remove the explicit document start (`---`) for `yaml`-files. For example:

Set to `true`:
```yaml
---
project_name: yamlfix
```

Set to `false`:
```yaml
project_name: yamlfix
```

### Sequence (List) Style

Default: `sequence_style: YamlNodeStyle = YamlNodeStyle.FLOW_STYLE`<br>
Environment variable override:
```bash
export YAMLFIX_SEQUENCE_STYLE="flow_style"
```

Available values: `flow_style`, `block_style`, `keep_style`

Transform sequences (lists) to either flow-style, block-style or leave them as-is. If enabled `yamlfix` will also ensure, that flow-style lists are automatically converted to block-style if the resulting key+list elements would breach the line-length. For example:

Set to `true` (flow-style):
```yaml
---
list: [item, item, item]
```

Set to `false` (block-style):
```yaml
---
list:
  - item
  - item
  - item
```

### Indentation

Default:
`indent_mapping: int = 2`
`indent_offset: int = 2`
`indent_sequence: int = 4`
Environment variable override:
```bash
export YAMLFIX_INDENT_MAPPING="2"
export YAMLFIX_INDENT_OFFSET="2"
export YAMLFIX_INDENT_SEQUENCE="4"
```

Provide the `ruyaml` configuration for indentation of mappings (dicts) and sequences (lists) and the indentation offset for elements. See the `ruyaml` configuration documentation: https://ruyaml.readthedocs.io/en/latest/detail.html#indentation-of-block-sequences

### Line Length (Width)

Default: `line_length: int = 80`<br>
Environment variable override:
```bash
export YAMLFIX_LINE_LENGTH="80"
```

Configure the line-length / width configuration for `ruyaml`. With this configuration long multiline-strings will be wrapped at that point and flow-style lists will be converted to block-style if they are longer than the provided value.

### `None` Representation

Default: `none_representation: str = ""`<br>
Environment variable override:
```bash
export YAMLFIX_LINE_LENGTH=""
```

In `yaml`-files an absence of a value can be described in multiple canonical ways. This configuration enforces a user-defined representation for `None` values. For example:

Valid `None` representation values are `(empty string)`, `null`, `Null`, `NULL`, `~`.

Provided the source yaml file looks like this:
```yaml
none_value1:
none_value2: null
none_value3: Null
none_value4: NULL
none_value5: ~
```

The default behaviour (empty string) representation would look like this:
```yaml
none_value1:
none_value2:
none_value3:
none_value4:
none_value5:
```

With this option set to `none_representation="null"` it would look like this:
```yaml
none_value1: null
none_value2: null
none_value3: null
none_value4: null
none_value5: null
```

### Quote Basic Values

Default: `quote_basic_values: bool = False`<br>
Environment variable override:
```bash
export YAMLFIX_quote_basic_values="false"
```

Per default `ruyaml` will quote only values where it is necessary to explicitly define the type of a value. This is the case for numbers and boolean values for example. If your `yaml`-file contains a value of type string that would look like a number, then this value needs to be quoted.

This option allows for quoting of all simple values in mappings (dicts) and sequences (lists) to enable a homogeneous look and feel for string lists / simple key/value mappings. For example:

```yaml
# option set to false
stringKey1: abc
stringKey2: "123"
stringList: [abc, "123"]
```

```yaml
# option set to true
stringKey1: "abc"
stringKey2: "123"
stringList: ["abc", "123"]
```

### Quote Keys and Basic Values

Default: `quote_keys_and_basic_values: bool = False`<br>
Environment variable override:
```bash
export YAMLFIX_quote_keys_and_basic_values="false"
```

Similar to the [quote basic values](#quote-basic-values) configuration option, this option, in addition to the values themselves, quotes the keys as well. For example:

```yaml
# option set to false
key: value
list: [item, item]
```

```yaml
# option set to true
"key": "value"
"list": ["item", "item"]
```

### Quote Representation

Default: `quote_representation: str = "'"`<br>
Environment variable override:
```bash
export YAMLFIX_quote_representation="'"
```

Configure which quotation string is used for quoting values. For example:

```yaml
# Option set to: '
key: 'value'
```

```yaml
# Option set to: "
key: "value"
```

# References

As most open sourced programs, `yamlfix` is standing on the shoulders of giants,
namely:

[yamlfmt](https://github.com/mmlb/yamlfmt) : Inspiration and alternative of this
program. I created a new one because the pace of their pull requests is really
slow, they don't have tests, CI pipelines or documentation.

[ruyaml](https://github.com/pycontribs/ruyaml) : A git based community
maintained for of [ruamel](https://yaml.readthedocs.io/en/latest/) yaml parser.

[Click](https://click.palletsprojects.com/) : Used to create the command line
interface.

[maison](https://github.com/dbatten5/maison) : Used for finding, reading and parsing the configuration options.

[Pytest](https://docs.pytest.org/en/latest) : Testing framework, enhanced by the
awesome [pytest-cases](https://smarie.github.io/python-pytest-cases/) library
that made the parametrization of the tests a lovely experience.

[Mypy](https://mypy.readthedocs.io/en/stable/) : Python static type checker.

[Flakeheaven](https://github.com/flakeheaven/flakeheaven) : Python linter with
[lots of checks](https://lyz-code.github.io/blue-book/devops/flakeheaven#plugins).

[Black](https://black.readthedocs.io/en/stable/) : Python formatter to keep a
nice style without effort.

[Autoimport](https://lyz-code.github.io/autoimport) : Python formatter to
automatically fix wrong import statements.

[isort](https://github.com/timothycrosley/isort) : Python formatter to order the
import statements.

[PDM](https://pdm.fming.dev/) : Command line tool to manage the dependencies.

[Mkdocs](https://www.mkdocs.org/) : To build this documentation site, with the
[Material theme](https://squidfunk.github.io/mkdocs-material).

[Safety](https://github.com/pyupio/safety) : To check the installed dependencies
for known security vulnerabilities.

[Bandit](https://bandit.readthedocs.io/en/latest/) : To finds common security
issues in Python code.

# Contributing

For guidance on setting up a development environment, and how to make a
contribution to `yamlfix`, see
[Contributing to yamlfix](https://lyz-code.github.io/yamlfix/contributing).

# Donations

<a href="https://liberapay.com/Lyz/donate"><img alt="Donate using
Liberapay" src="https://liberapay.com/assets/widgets/donate.svg"></a>
or
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/T6T3GP0V8)

If you are using some of my open-source tools, have enjoyed them, and want to
say "thanks", this is a very strong way to do it.

If your product/company depends on these tools, you can sponsor me to ensure I
keep happily maintaining them.

If these tools are helping you save money, time, effort, or frustrations; or
they are helping you make money, be more productive, efficient, secure, enjoy a
bit more your work, or get your product ready faster, this is a great way to
show your appreciation. Thanks for that!

And by sponsoring me, you are helping make these tools, that already help you,
sustainable and healthy.
