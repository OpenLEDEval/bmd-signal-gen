# Developer Documentation

This document provides step-by-step setup instructions and development standards for contributing to the BMD Signal Generator project.

## Quick Start for New Contributors

### 1. Prerequisites

Before you begin, ensure you have:

- **Python 3.13+** installed
- **UV package manager** ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Blackmagic Design Desktop Video drivers** (latest version)
- **Blackmagic Design DeckLink SDK 14.4** 
- **clang++ with C++20 support** (macOS) or equivalent C++ compiler

### 2. Get the DeckLink SDK

1. Download the DeckLink SDK 14.4 from [Blackmagic Design Support](https://www.blackmagicdesign.com/support/download/af37b96d1b9a4a1cbe3f5d4e3b7c8cdb/Mac%20OS%20X)
2. Extract the SDK and locate the headers directory
3. **Important**: Place the SDK headers in the correct location:
   ```bash
   # Create the expected directory structure
   mkdir -p cpp/include/DeckLinkAPI
   
   # Copy SDK headers to the project
   cp /path/to/decklink-sdk/Mac/include/* cpp/include/DeckLinkAPI/
   ```

### 3. Project Setup

```bash
# Clone the repository
git clone <repository-url>
cd bmd-signal-gen

# Install all dependencies (including dev tools)
uv sync

# Build the C++ library and Python package
uv run invoke build

# Install pre-commit hooks for code quality
uv run pre-commit install

# Verify everything works
uv run invoke check
```

### 4. Verify Installation

Test that everything is working:

```bash
# Run the CLI to see available commands
uv run python -m bmd_sg.cli.main --help

# Run tests
uv run invoke test

# Check code quality
uv run invoke check
```

## Project Overview

The BMD Signal Generator is a cross-platform tool for generating test patterns via Blackmagic Design DeckLink devices. It consists of multiple components:

- **C++ Core**: Low-level DeckLink SDK wrapper (`cpp/`)
- **Python Library**: High-level interface with ctypes bindings (`bmd_sg/`)
- **REST API**: FastAPI-based HTTP interface
- **CLI Tool**: Command-line interface for direct usage

## Development Workflow

### Code Quality Management with Invoke

This project uses [Invoke](https://www.pyinvoke.org/) for task automation and code quality maintenance. All development tasks are automated through invoke commands.

**Essential commands:**
```bash
uv run invoke build     # Build C++ library and Python package
uv run invoke check     # Run all checks (lint, format, typecheck)
uv run invoke fix       # Auto-fix issues and format code
uv run invoke test      # Run pytest test suite
uv run invoke dev       # Quick cycle: fix + test
```

**Individual tools:**
```bash
uv run invoke lint            # Run ruff linting
uv run invoke lint --fix      # Auto-fix linting issues
uv run invoke format          # Format code with ruff
uv run invoke typecheck       # Run pyright type checking
uv run invoke clean           # Clean build artifacts
```

### Typical Development Workflow

**Starting new work:**
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
uv run invoke build           # Ensure clean build
```

**During development:**
```bash
# Make your changes...
uv run invoke fix             # Fix formatting and linting
uv run invoke test            # Run tests
```

**Before committing:**
```bash
uv run invoke dev             # Complete check: fix + test
git add .
git commit -m "your commit message"
```

**Pre-commit hooks will automatically run:**
- Code formatting checks
- Linting validation
- Basic quality checks

### Build System

The build process is automated through invoke:

```bash
uv run invoke build
```

This command:
1. Cleans previous build artifacts
2. Compiles the C++ library (`libdecklink.dylib`)
3. Builds the Python package
4. Validates the build succeeded

**Manual build (if needed):**
```bash
cd cpp
make clean && make
cd ..
```

### Pre-commit Hooks

Pre-commit hooks are automatically installed during setup and run on every commit to ensure code quality. They check:

- Code formatting (ruff format)
- Linting rules (ruff check) 
- Import sorting
- Basic type checking

If hooks fail, fix the issues and commit again:
```bash
uv run invoke fix  # Fix most issues automatically
git add .
git commit -m "your message"
```

## Code Standards

### Documentation
- Use NumPy-style docstrings for public functions and classes
- Include type hints for all function parameters and return values
- Add examples in docstrings for complex functionality

### Code Quality
- Follow PEP 8 style guidelines (enforced by ruff)
- Maximum line length: 88 characters
- Use meaningful variable and function names
- Handle errors with appropriate exceptions and messages

### Testing
- Write tests for new functionality using pytest
- Mock external dependencies (hardware, network calls)
- Test error conditions and edge cases

## Contributing

1. Create feature branch from `main`
2. Make changes following code standards
3. Run `uv run invoke dev` to test and fix issues
4. Submit pull request with clear description

All code is reviewed before merging to ensure quality and consistency.