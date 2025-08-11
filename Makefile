.PHONY: setup check test

setup:
	@echo "--- Checking environment ---"
	@command -v uv >/dev/null 2>&1 || { echo >&2 "uv is not installed. Please install it: https://github.com/astral-sh/uv"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo >&2 "docker is not installed. Please install it."; exit 1; }
	@echo "--- Syncing environment ---"
	uv sync --all-extras

check:
	@echo "--- Running checks ---"
	.venv/bin/pre-commit run --all-files

test:
	@echo "--- Running tests ---"
	.venv/bin/pytest
