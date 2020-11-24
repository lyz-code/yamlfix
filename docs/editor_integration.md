For a smother experience, you can run `yamlfix` each time you save your file
in your editor.

# Vim

To integrate `yamlfix` into Vim, I recommend using the [ale
plugin](https://github.com/dense-analysis/ale).

!!! note ""

    If you are new to ALE, check [this
    post](https://lyz-code.github.io/blue-book/linux/vim/vim_plugins/#ale).

There's a [pull request](https://github.com/dense-analysis/ale/pull/3461) open
to run `yamlfix` automatically by default. Until it's merged you can either:

* Copy the `autoload/ale/fixers/yamlfix.vim` file into your `fixers`
    directory and edit `autoload/ale/fix/registry.vim` to match the contents of
    the pull request.
* Use the `feat/add-yamlfixer` branch of my [ale
    fork](https://github.com/lyz-code/ale/tree/feat/add-yamlfix) as
    your ale directory.
