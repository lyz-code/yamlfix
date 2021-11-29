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
