.PHONY: help test build clean

VENV=./venv
PYTHON=$(VENV)/bin/python
BUILD_DIR=./build

.DEFAULT : help

help:
	@echo "This Makefile provides the following targets:"
	@echo "    build: package the application as a PEX file under $(BUILD_DIR)"
	@echo "    clean: remove the built artifacts directory, the build venv and all caches"
	@echo "    test: run the included tests"
	@echo "    help: show this message"

build: venv
	@echo "Packaging the application..."
	test -d $(BUILD_DIR) || mkdir $(BUILD_DIR)
	$(PYTHON) -m pex -r requirements.txt -D hik -o $(BUILD_DIR)/himakura.pex -e main
	@echo "Done."

clean:
	@echo "Cleaning up..."
	(test -d $(BUILD_DIR) && rm -r $(BUILD_DIR)) || true
	(test -d $(VENV) && rm -r $(VENV)) || true
	find . -name '__pycache__' -type d -exec rm -r {} +
	@echo "Done."

test: venv
	@echo "Running tests..."
	$(PYTHON) -m unittest
	@echo "Done."

venv: requirements.txt
	@echo "Creating the virtualenv..."
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install pex
	$(PYTHON) -m pip install -r requirements.txt
	@echo "Done."
