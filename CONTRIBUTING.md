# Contributing to Eldercrank Stripe Core

Thank you for considering contributing to the Eldercrank Stripe Core project! We appreciate your interest in improving this library.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate in all interactions.

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker to report bugs
- Describe the problem in detail
- Include steps to reproduce the issue
- Provide information about your environment (OS, Python version, etc.)

### Suggesting Features

- Use the GitHub issue tracker to suggest new features
- Explain the use case for the feature
- Discuss potential implementation approaches

### Submitting Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Add your changes with appropriate tests
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request with a clear description

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager

### Getting Started

```bash
# Clone your fork
git clone <your-fork-url>
cd eldercrank-stripe-core

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

## Code Standards

### Python Code

- Follow PEP 8 style guide
- Use type hints for all public functions
- Write docstrings for all public functions and classes
- Keep functions and methods focused and concise

### Testing

- Write tests for all new functionality
- Ensure all tests pass before submitting
- Aim for high test coverage

### Documentation

- Update documentation for any changes to the public API
- Include usage examples where appropriate
- Keep README files up to date

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality:

- `ruff` for linting and formatting
- These run automatically on commit

Make sure to install them with:

```bash
uv run pre-commit install
```

## Pull Request Process

1. Ensure your PR addresses a single issue or adds a single feature
2. Update the README.md if needed
3. Add tests for new functionality
4. Ensure all tests pass
5. Wait for review and address any feedback

## Questions?

If you have questions about contributing, feel free to open an issue for discussion.

Thank you for contributing!
