# Python Container

This container provides a Python environment for executing LLM-generated Python code.

## Prerequisites

- **Python**: Version 3.12 or higher
- **Poetry**: For dependency management

## Installation

### Installing Python

#### macOS
```bash
# Using Homebrew
brew install python@3.12

# Or use pyenv for version management
brew install pyenv
pyenv install 3.12
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get install python3.12 python3.12-venv

# Fedora
sudo dnf install python3.12

# Using pyenv (recommended for version management)
curl https://pyenv.run | bash
pyenv install 3.12
```

#### Windows
Download the installer from https://www.python.org/downloads/

### Installing Poetry

```bash
# Official installer (recommended)
curl -sSL https://install.python-poetry.org | python3 -

# Or using pip
pip install poetry

# Or using Homebrew (macOS)
brew install poetry
```

## Dependencies

Dependencies are managed through `pyproject.toml`:

### Runtime Dependencies
- **requests**: HTTP library for making API calls

### Development Dependencies
- **pylint**: Code analysis and linting tool
- **ruff**: Fast Python linter (installed but not actively used)

## Usage

The benchmark framework will:
1. Write Python code to `main.py`
2. Run code validation using `pylint`
3. Execute the code using Poetry: `poetry run python main.py`

## Commands Used by Benchmark

- **Install dependencies**: `poetry install`
- **Validate**: `poetry run pylint --output-format=json main.py`
- **Run**: `poetry run python main.py`

## Project Structure

```
python_container/
├── pyproject.toml    # Project configuration and dependencies
├── poetry.lock       # Locked dependency versions
└── main.py          # Main source file (replaced during benchmark)
```

## Notes

- Poetry creates a virtual environment automatically
- The container uses modern Python packaging standards
- All dependencies are isolated from the system Python
- The benchmark may use various Python standard library modules