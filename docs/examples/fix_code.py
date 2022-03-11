from yamlfix import fix_code

source_code = "a: 1"

fixed_code = fix_code(source_code)

assert fixed_code == "---\na: 1\n"
