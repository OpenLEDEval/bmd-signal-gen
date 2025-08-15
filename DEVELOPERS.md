# Developer Documentation

Setup instructions and development standards for the BMD Signal Generator project.

## Quick Start

### Prerequisites
- **Python 3.13+**, **UV package manager**, **Desktop Video drivers**, **DeckLink SDK 14.4**, **clang++ with C++20**

### DeckLink SDK Setup
1. Download DeckLink SDK 14.4 from [Blackmagic Design Support](https://www.blackmagicdesign.com/support/download/af37b96d1b9a4a1cbe3f5d4e3b7c8cdb/Mac%20OS%20X)
2. Place headers: `mkdir -p cpp/include/DeckLinkAPI && cp /path/to/sdk/Mac/include/* cpp/include/DeckLinkAPI/`

### Project Setup
```bash
git clone <repository-url> && cd bmd-signal-gen
uv sync                              # Install dependencies
uv run invoke build                  # Build C++ library and Python package
uv run pre-commit install           # Install code quality hooks
uv run invoke check                  # Verify everything works
```

### Verification
```bash
uv run bmd-signal-gen --help  # CLI help
uv run invoke test                        # Run tests
```

## Development Workflow

**Architecture**: C++ Core (`cpp/`) + Python Library (`bmd_sg/`) + CLI Tool + REST API  
**Build System**: Invoke task automation - see `CLAUDE.md` Common Commands section

### Typical Workflow
```bash
git checkout -b feature/name && uv run invoke build  # Start new work
# Make changes...
uv run invoke fix && uv run invoke test              # During development  
uv run invoke dev && git add . && git commit        # Before committing
```

**Pre-commit hooks** auto-run: formatting, linting, basic type checking  
**Manual build**: `cd cpp && make clean && make && cd ..`

## Code Standards

**Documentation**: NumPy-style docstrings with type hints, parameters, examples  
**Code Quality**: PEP 8 (88 char limit), meaningful names, specific exception handling  
**Testing**: pytest with mocked dependencies, test error conditions and edge cases  

## Contributing

1. Create feature branch from `main`
2. Follow code standards, run `uv run invoke dev`
3. Submit PR with clear description
4. Code review required before merge