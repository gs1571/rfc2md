.PHONY: help install install-dev lint format type-check test clean all

help:
	@echo "Available commands:"
	@echo "  make install           - Install production dependencies"
	@echo "  make install-dev       - Install development dependencies"
	@echo "  make lint              - Run ruff linter"
	@echo "  make format            - Format code with ruff"
	@echo "  make type-check        - Run mypy type checker"
	@echo "  make test              - Run all tests with pytest"
	@echo "  make test-unit         - Run only unit tests"
	@echo "  make test-integration  - Run only integration tests"
	@echo "  make update-snapshots  - Update all test snapshots"
	@echo "  make all               - Run all checks (lint, format-check, type-check, test)"
	@echo "  make clean             - Remove cache and build artifacts"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

lint:
	@echo "Running ruff linter..."
	ruff check .

format:
	@echo "Formatting code with ruff..."
	ruff format .

format-check:
	@echo "Checking code formatting..."
	ruff format --check .

type-check:
	@echo "Running mypy type checker..."
	mypy rfc2md.py lib/

test:
	@echo "Running all tests..."
	pytest --cov=lib --cov-report=term-missing --cov-report=html

test-unit:
	@echo "Running unit tests..."
	pytest -m "not integration" --cov=lib --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	pytest -m integration -v

update-snapshots:
	@echo "Updating all snapshots..."
	@echo "Updating XML snapshots..."
	@for file in tests/fixtures/xml/*.xml; do \
		if [ -f "$$file" ]; then \
			base=$$(basename "$$file" .xml); \
			echo "  Updating $$base..."; \
			source .venv/bin/activate && python rfc2md.py --file "$$file" --output "tests/snapshots/$$base.md"; \
		fi \
	done
	@echo "Updating HTML snapshots..."
	@for file in tests/fixtures/html/*.html; do \
		if [ -f "$$file" ]; then \
			base=$$(basename "$$file" .html); \
			echo "  Updating $$base..."; \
			source .venv/bin/activate && python rfc2md.py --file "$$file" --output "tests/snapshots/$$base.md"; \
		fi \
	done
	@echo "All snapshots updated!"

all: lint format-check type-check test
	@echo "All checks passed!"

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@echo "Cleanup complete!"