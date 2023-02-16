For a smoother experience, you can run `yamlfix` automatically each time each
time you save your file in your editor or when you run `git commit`.

# Vim

To integrate `yamlfix` into Vim, I recommend using the [ale
plugin](https://github.com/dense-analysis/ale).

!!! note ""

    If you are new to ALE, check [this
    post](https://lyz-code.github.io/blue-book/linux/vim/vim_plugins/#ale).

`ale` is configured to run `yamlfix` automatically by default.

# [pre-commit](https://pre-commit.com/)

You can run `yamlfix` before we do a commit using the
[pre-commit](https://pre-commit.com/) framework. If you don't know how to use
it, follow [these
guidelines](https://lyz-code.github.io/blue-book/devops/ci/#configuring-pre-commit).

You'll need to add the following lines to your project's
`.pre-commit-config.yaml` file.

```yaml
repos:
  - repo: https://github.com/lyz-code/yamlfix/
    rev: main
    hooks:
      - id: yamlfix
```
