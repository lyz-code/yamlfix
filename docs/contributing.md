We'd love you to contribute to *yamlfix*!

## Issues

Questions, feature requests and bug reports are all welcome as issues.
**To report a security vulnerability, please see our [security
policy](https://github.com/lyz-code/yamlfix/security/policy) instead.**

To make it as simple as possible for us to help you, please include the output
of the following call in your issue:

```bash
python -c "import yamlfix.version; print(yamlfix.version.version_info())"
```

or if you have `make` installed, you can use `make version`.

Please try to always include the above unless you're unable to install `yamlfix` or know it's not relevant to your question or
feature request.

## Pull Requests

*yamlfix* is released regularly so you should see your
improvements release in a matter of days or weeks.

!!! note
    Unless your change is trivial (typo, docs tweak etc.), please create an
    issue to discuss the change before creating a pull request.

If you're looking for something to get your teeth into, check out the ["help
wanted"](https://github.com/lyz-code/yamlfix/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22)
label on github.

## Development facilities

To make contributing as easy and fast as possible, you'll want to run tests and
linting locally.

!!! note ""
    **tl;dr**: use `make format` to fix formatting, `make` to run tests and linting & `make docs`
    to build the docs.

You'll need to have python 3.6, 3.7, or 3.8, virtualenv, git, and make installed.

* Clone your fork and go into the repository directory:

    ```bash
    git clone git@github.com:<your username>/yamlfix.git
    cd yamlfix
    ```

* Set up the virtualenv for running tests:

    ```bash
    virtualenv -p `which python3.7` env
    source env/bin/activate
    ```

* Install yamlfix, dependencies and configure the
    pre-commits:

    ```bash
    make install
    ```

* Checkout a new branch and make your changes:

    ```bash
    git checkout -b my-new-feature-branch
    ```

* Fix formatting and imports: yamlfix uses
    [black](https://github.com/ambv/black) to enforce formatting and
    [isort](https://github.com/timothycrosley/isort) to fix imports.

    ```bash
    make format
    ```

* Run tests and linting:

    ```bash
    make
    ```

    There are more sub-commands in Makefile like `test-code`, `test-examples`,
    `mypy` or `security` which you might want to use, but generally `make`
    should be all you need.

    If you need to pass specific arguments to pytest use the `ARGS` variable,
    for example `make test ARGs='-k test_markdownlint_passes'`.

* Build documentation: If you have changed the documentation, make sure it
    builds the static site. Once built it will serve the documentation at
    `localhost:8000`:

    ```bash
    make docs
    ```

* Commit, push, and create your pull request.
