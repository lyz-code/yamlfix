.DEFAULT_GOAL := test
isort = pdm run isort src tests
black = pdm run black --target-version py37 src tests

.PHONY: install
install:
	pdm install --dev
	pdm run pre-commit install

.PHONY: update
update:
	@echo "-------------------------"
	@echo "- Updating dependencies -"
	@echo "-------------------------"

	pdm update --no-sync
	pdm sync --clean

	@echo "\a"

.PHONY: update-production
update-production:
	@echo "------------------------------------"
	@echo "- Updating production dependencies -"
	@echo "------------------------------------"

	pdm update --production --no-sync
	pdm sync --clean

	@echo "\a"

.PHONY: outdated
outdated:
	@echo "-------------------------"
	@echo "- Outdated dependencies -"
	@echo "-------------------------"

	pdm update --dry-run --unconstrained

	@echo "\a"

.PHONY: format
format:
	@echo "----------------------"
	@echo "- Formating the code -"
	@echo "----------------------"

	$(isort)
	$(black)

	@echo ""

.PHONY: lint
lint:
	@echo "--------------------"
	@echo "- Testing the lint -"
	@echo "--------------------"

	pdm run flakeheaven lint src/ tests/
	$(isort) --check-only --df
	$(black) --check --diff

	@echo ""

.PHONY: mypy
mypy:
	@echo "----------------"
	@echo "- Testing mypy -"
	@echo "----------------"

	pdm run mypy src tests

	@echo ""

.PHONY: test
test: test-code test-examples

	@echo "\a"

.PHONY: test-code
test-code:
	@echo "----------------"
	@echo "- Testing code -"
	@echo "----------------"

	pdm run pytest --cov-report term-missing --cov src tests/* ${ARGS}

	@echo ""

.PHONY: test-examples
test-examples:
	@echo "--------------------"
	@echo "- Testing examples -"
	@echo "--------------------"

	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'echo {}; pdm run python {} >/dev/null 2>&1 || (echo "{} failed" ; exit 1)'
	@echo ""

	# pdm run pytest docs/examples/*

	@echo ""

.PHONY: all
all: lint mypy test security build-docs

	@echo "\a"

.PHONY: clean
clean:
	@echo "---------------------------"
	@echo "- Cleaning unwanted files -"
	@echo "---------------------------"

	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*.rej' `
	rm -rf `find . -type d -name '*.egg-info' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -f src/*.c pydantic/*.so
	rm -rf site
	rm -rf docs/_build
	rm -rf docs/.changelog.md docs/.version.md docs/.tmp_schema_mappings.html
	rm -rf codecov.sh
	rm -rf coverage.xml

	@echo ""

.PHONY: docs
docs: test-examples
	@echo "-------------------------"
	@echo "- Serving documentation -"
	@echo "-------------------------"

	pdm run mkdocs serve

	@echo ""

.PHONY: bump
bump: pull-main bump-version build-package upload-pypi clean

	@echo "\a"

.PHONY: pull-main
pull-main:
	@echo "------------------------"
	@echo "- Updating repository  -"
	@echo "------------------------"

	git checkout main
	git pull

	@echo ""

.PHONY: build-package
build-package: clean
	@echo "------------------------"
	@echo "- Building the package -"
	@echo "------------------------"

	pdm build

	@echo ""

.PHONY: build-docs
build-docs:
	@echo "--------------------------"
	@echo "- Building documentation -"
	@echo "--------------------------"

	pdm run mkdocs build --strict

	@echo ""

.PHONY: upload-pypi
upload-pypi:
	@echo "-----------------------------"
	@echo "- Uploading package to pypi -"
	@echo "-----------------------------"

	twine upload -r pypi dist/*

	@echo ""

.PHONY: bump-version
bump-version:
	@echo "---------------------------"
	@echo "- Bumping program version -"
	@echo "---------------------------"

	pdm run cz bump --changelog --no-verify
	git push
	git push --tags

	@echo ""

.PHONY: security
security:
	@echo "--------------------"
	@echo "- Testing security -"
	@echo "--------------------"

	pdm run safety check
	@echo ""
	pdm run bandit -r src

	@echo ""

.PHONY: version
version:
	@python -c "import yamlfix.version; print(yamlfix.version.version_info())"
