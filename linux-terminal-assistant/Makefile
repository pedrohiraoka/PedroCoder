# Makefile for Linux Terminal Assistant (LTA)

.PHONY: help install dev test lint format clean build run check-deps

# Default target
help:
	@echo "Linux Terminal Assistant - Available targets:"
	@echo ""
	@echo "  install      - Install LTA in production mode"
	@echo "  dev          - Set up development environment"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run code linters (ruff, mypy)"
	@echo "  format       - Format code with black"
	@echo "  clean        - Remove build artifacts and venv"
	@echo "  build        - Build distribution packages"
	@echo "  run          - Run LTA in interactive mode"
	@echo "  check-deps   - Check external tool dependencies"
	@echo ""

# Install in production mode
install:
	pip install .

# Set up development environment
dev:
	@if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
	fi
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -e ".[dev]"
	@echo "Development environment ready!"
	@echo "Activate with: source venv/bin/activate"

# Run tests
test:
	. venv/bin/activate && pytest src/lta/tests -v --cov=lta --cov-report=term-missing

# Run linters
lint:
	. venv/bin/activate && ruff check src/
	. venv/bin/activate && mypy src/lta --ignore-missing-imports

# Format code
format:
	. venv/bin/activate && black src/
	. venv/bin/activate && ruff check src/ --fix

# Clean build artifacts
clean:
	rm -rf venv/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned!"

# Build distribution packages
build:
	. venv/bin/activate && pip install build
	. venv/bin/activate && python -m build

# Run LTA
run:
	. venv/bin/activate && lta

# Check external dependencies
check-deps:
	. venv/bin/activate && lta check

# Install system dependencies (Ubuntu/Debian)
install-system-deps:
	sudo apt update
	sudo apt install -y yt-dlp fzf jq ripgrep bat docker.io

# Install system dependencies (Fedora)
install-system-deps-fedora:
	sudo dnf install -y yt-dlp fzf jq ripgrep bat docker

# Install system dependencies (Arch)
install-system-deps-arch:
	sudo pacman -S --noconfirm yt-dlp fzf jq ripgrep bat docker

# Create config directory
setup-config:
	mkdir -p ~/.config/lta
	cp config/defaults.yaml ~/.config/lta/config.yaml || true
	@echo "Configuration set up at ~/.config/lta/config.yaml"
