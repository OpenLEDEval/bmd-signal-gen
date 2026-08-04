# Developer Documentation

Setup instructions and development standards for the BMD Signal Generator project.

## Quick Start

### Prerequisites
- **Python 3.12+**, **UV package manager**, **Desktop Video drivers**

DeckLink access comes from
[pydecklink](https://github.com/Fuse-Technical-Group/pydecklink), installed
from PyPI by `uv sync`. No SDK download or C++ toolchain is required.

### Project Setup
```bash
git clone <repository-url> && cd bmd-signal-gen
uv sync                              # Install dependencies (incl. pydecklink)
uv run pre-commit install           # Install code quality hooks
uv run invoke check                  # Verify everything works
```

### Verification
```bash
uv run bmd-signal-gen --help  # CLI help
uv run invoke test                        # Run tests
```

## Development Workflow

**Architecture**: Python Library (`bmd_sg/`) over pydecklink + CLI Tool + REST API  
**Build System**: Invoke task automation - see `CLAUDE.md` Common Commands section

### Typical Workflow
```bash
git checkout -b feature/name                         # Start new work
# Make changes...
uv run invoke fix && uv run invoke test              # During development  
uv run invoke dev && git add . && git commit        # Before committing
```

**Pre-commit hooks** auto-run: formatting, linting, basic type checking

## Code Standards

**Documentation**: NumPy-style docstrings with type hints, parameters, examples  
**Code Quality**: PEP 8 (88 char limit), meaningful names, specific exception handling  
**Testing**: pytest with mocked dependencies, test error conditions and edge cases  

## Contributing

1. Create feature branch from `main`
2. Follow code standards, run `uv run invoke dev`
3. Submit PR with clear description
4. Code review required before merge