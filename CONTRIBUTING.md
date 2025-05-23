# Contributing to Deep Search Persist

Thank you for your interest in contributing to Deep Search Persist! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Adding Dependencies](#adding-dependencies)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
   ```bash
   git clone https://github.com/YOUR-USERNAME/deep-search-persist.git
   cd deep-search-persist
   ```
3. Set up the development environment
   ```bash
   # Install with development dependencies
   pip install .[dev]
   ```

## Development Workflow

### Pre-commit Hooks (Required)

This project uses [pre-commit](https://pre-commit.com/) to automate code formatting, linting, and type checking before each commit.

**Setup pre-commit after cloning:**

```bash
pip install pre-commit  # (if not already installed)
pre-commit install
```

This will ensure all configured hooks (black, flake8, mypy, etc.) run automatically when you commit code. You can also run all hooks manually:

```bash
pre-commit run --all-files
```

### Branching and PRs

1. Create a new branch for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/your-bugfix-name
   ```

2. Make your changes and commit them with clear, descriptive commit messages
   ```bash
   git commit -m "Add feature: description of your feature"
   ```

3. Push your branch to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request against the main repository

## Adding Dependencies

This project uses a modular requirements system:

1. Dependencies are organized in separate files in the `requirements/` directory
2. Each file follows the naming convention `requirements-{group}.txt`
3. To add a new dependency group:
   - Create a new file in the `requirements/` directory (e.g., `requirements-newfeature.txt`)
   - Add your dependencies to this file
   - The build engine will automatically discover this file and create a corresponding install option
   - Users can then install with `pip install .[newfeature]`
4. To add to an existing group, simply add the dependency to the appropriate file

**Important Notes:**
- Do not create a `requirements-all.txt` file as 'all' is a special key that is dynamically generated
- Main requirements should go in the root `requirements.txt` file
- Keep each dependency group focused on a specific purpose

## MongoDB and Session Persistence

Sessions are now persisted in MongoDB (see the main README and `docker/docker-compose.persist.yml`).

- When developing or testing session features, ensure you have MongoDB running (use Docker Compose for easiest setup).
- All session management (save, load, list, delete, resume, rollback) is handled via the `SessionPersistenceManager`.
- When adding new user-facing fields to the research session or web UI, ensure they are also persisted in MongoDB by updating the relevant models and serialization logic.

## Testing

Before submitting a Pull Request, please run the tests to ensure your changes don't break existing functionality:

```bash
# Run the test suite
pytest

# Run with coverage report
pytest --cov=deep_search_persist

# Run type checking
mypy deep_search_persist
```

## Pull Request Process

1. Ensure your code passes all tests and linting checks
2. Update the documentation to reflect any changes in functionality
3. Include tests for new features or bug fixes
4. Your PR should target the `main` branch
5. A maintainer will review your PR and may request changes
6. Once approved, a maintainer will merge your PR

## Style Guidelines

- Follow PEP 8 style guidelines for Python code
- Use [Black](https://github.com/psf/black) for code formatting
- Use type hints where appropriate
- Write docstrings for all public functions, classes, and methods
- Keep line length to a maximum of 88 characters (Black's default)

Thank you for contributing to Deep Search Persist!
