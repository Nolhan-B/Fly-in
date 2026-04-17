PYTHON = python3
MAIN = main.py
MAP = test-map.txt

.PHONY: install run debug clean lint lint-strict

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

run:
	@echo "Running simulation..."
	$(PYTHON) $(MAIN) $(MAP)

debug:
	@echo "Debug mode (pdb)..."
	$(PYTHON) -m pdb $(MAIN)

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	@echo "Clean done."

lint:
	@echo "Running flake8..."
	flake8 .
	@echo "Running mypy..."
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@echo "Running strict checks..."
	flake8 .
	mypy . --strict