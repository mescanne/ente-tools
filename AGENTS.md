# Agent Instructions

This document provides instructions for AI agents working on this repository.

## Development Setup

1.  **Install dependencies:** Run `make setup` to create a virtual environment and install all necessary dependencies. This uses `uv` to manage the environment.

## Running Checks and Tests

Before submitting any changes, you **must** run all checks and tests to ensure the code is clean and functional.

1.  **Run static analysis and formatting checks:**
    ```bash
    make check
    ```
    This command runs `pyright` for type checking and `ruff` for linting and formatting. Ensure all checks pass before proceeding.

2.  **Run the test suite:**
    ```bash
    make test
    ```
    This command runs the `pytest` test suite. All tests must pass.

## Pre-commit Hooks

This repository uses pre-commit hooks to automatically run checks before each commit. The hooks are defined in `.pre-commit-config.yaml`. The `make check` command has been configured to run these hooks.

## Best Practices

*   **Always run `make check` and `make test` before submitting.** This is crucial to maintain code quality.
*   When adding new features, also add corresponding tests.
*   Keep the `AGENTS.md` file updated if you introduce new tools or change the development workflow.
