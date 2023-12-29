#
# SPDX-License-Identifier: BSD-3-clause
# Copyright (c) nexB Inc. and contributors
# See https://github.com/nexB/flot/ for support and sources

# Python version can be specified with `$ PYTHON_EXE=python3.x make conf`
PYTHON_EXE?=python3
VENV=venv
ACTIVATE?=. ${VENV}/bin/activate;

virtualenv:
	@echo "-> Bootstrap the virtualenv with PYTHON_EXE=${PYTHON_EXE}"
	@${PYTHON_EXE} -m venv ${VENV}
	@${ACTIVATE} pip install --upgrade pip

conf: virtualenv
	@echo "-> Install dependencies"
	@${ACTIVATE} pip install --editable .

dev: virtualenv
	@echo "-> Configure and install development dependencies"
	@${ACTIVATE} pip install --editable .[test,doc]

build: test
	@echo "-> Building sdist and wheel"
	rm -rf build/ dist/
	${VENV}/bin/flot --pyproject pyproject.toml --sdist --wheel

publish: build
	@echo "-> Publish built sdist and wheel to PyPi"
	${VENV}/bin/twine upload dist/*

isort:
	@echo "-> Apply isort changes to ensure proper imports ordering"
	${VENV}/bin/isort .

black:
	@echo "-> Apply black code formatter"
	${VENV}/bin/black .

doc8:
	@echo "-> Run doc8 validation"
	@${ACTIVATE} doc8 --max-line-length 100 --ignore-path docs/_build/ --quiet docs/

valid: isort black

check: doc8
	@echo "-> Run pycodestyle (PEP8) validation"
	@${ACTIVATE} pycodestyle --max-line-length=100 --exclude=venv .
	@echo "-> Run isort imports ordering validation"
	@${ACTIVATE} isort --check-only .
	@echo "-> Run black validation"
	@${ACTIVATE} black --check .

clean:
	@echo "-> Clean the Python env"
	rm -rf ${VENV} build/ dist/ docs/_build/ pip-selfcheck.json .tox .pytest_cache/ .coverage
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

test: check
	@echo "-> Run the test suite"
	${ACTIVATE} ${PYTHON_EXE} -m pytest -vvs

bump:
	@echo "-> Bump the version"
	venv/bin/bump-my-version bump patch

docs:
	rm -rf docs/_build/
	@${ACTIVATE} sphinx-build docs/ docs/_build/

.PHONY: virtualenv conf dev build publish check valid isort clean test bump docs
