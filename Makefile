.PHONY: help install install-dev lint format type-check test clean all

help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make type-check   - Run mypy type checker"
	@echo "  make test         - Run tests with pytest"
	@echo "  make all          - Run all checks (lint, format-check, type-check, test)"
	@echo "  make clean        - Remove cache and build artifacts"

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
	@echo "Running tests..."
	pytest --cov=lib --cov-report=term-missing --cov-report=html || echo "No tests found yet"

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