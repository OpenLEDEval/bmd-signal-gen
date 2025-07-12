# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

This project is a cross-platform BMD (Blackmagic Design) signal generator that
outputs test patterns via DeckLink devices. It consists of:

- **C++ core**: Low-level DeckLink SDK wrapper with pixel format conversion
  (`cpp/`)
- **Python wrapper**: High-level interface via ctypes (`bmd_sg/`)
- **REST API**: FastAPI-based HTTP interface for pattern generation
- **CLI tool**: Command-line interface for direct pattern output

## Build Commands

### C++ Library

```bash
cd cpp && make clean && make && cd ..
```

This builds `bmd_sg/decklink/libdecklink.dylib` - the core dynamic library.

### Python Environment

```bash
# Install dependencies
uv sync

# Activate environment
source .venv/bin/activate
```

## Development Guidelines

### Critical Standards (from .cursor/rules/coding-standards.mdc)

- **DRY Principle**: Eliminate duplicate logic, especially switch/case
  statements for pixel formats
- **Centralized Logic**: Use helpers/utilities rather than repeating
  validation/conversion code
- **Refactor Immediately**: Don't defer deduplication - fix patterns when found
- **All Languages**: Apply DRY to C++, Python, and build scripts

### Documentation Standards

All Python code must use **Sphinx-compatible docstrings** following **NumPy
documentation standards**.

#### Required Documentation

1. **All public modules** must have comprehensive module-level docstrings
2. **All public classes** must have detailed class docstrings with Parameters,
   Attributes, Examples, and Notes sections
3. **All public functions and methods** must have complete docstrings with
   Parameters, Returns, Raises, and Examples sections
4. **All public constants and enums** must be documented with brief descriptions

#### NumPy Docstring Format

Use these sections in docstrings:

- **Parameters** - Document all parameters with types and descriptions
- **Returns** - Document return values with types and descriptions
- **Raises** - Document all exceptions that can be raised
- **Examples** - Include practical usage examples with expected output
- **Notes** - Important implementation details or performance considerations
- **See Also** - Cross-references to related functionality

#### Example Class Docstring

```python
class HDRMetadata(ctypes.Structure):
    """
    Complete HDR metadata structure for DeckLink output.

    This structure defines comprehensive HDR metadata including EOTF
    (Electro-Optical Transfer Function), display primaries, and luminance values.

    Parameters
    ----------
    eotf : int, optional
        EOTF type (0=Reserved, 1=SDR, 2=PQ, 3=HLG). Default is 3.
    max_display_luminance : float, optional
        Maximum display mastering luminance in cd/m². Default is 1000.0.

    Attributes
    ----------
    EOTF : int
        Electro-Optical Transfer Function type
    referencePrimaries : ChromaticityCoordinates
        Display color primaries and white point

    Examples
    --------
    Create HDR metadata with default values:

    >>> metadata = HDRMetadata()
    >>> print(f"EOTF: {metadata.EOTF}")
    EOTF: 3

    Notes
    -----
    The structure automatically sets Rec.2020 color primaries as defaults.
    """
```

#### Documentation Quality Requirements

- **Complete parameter documentation** - All parameters must be documented with
  types and descriptions
- **Practical examples required** - Include real-world usage examples
- **Exception documentation** - Document all exceptions that can be raised
- **Cross-references** - Use See Also sections to link related functionality
- **Consistent terminology** - Use the same terms throughout the project

### HDR Metadata Handling

The project supports complete HDR metadata with:

- EOTF (Electro-Optical Transfer Function) specification
- Display primaries (Rec2020 by default)
- Mastering display luminance values
- MaxCLL/MaxFALL content light levels
- **MaxCLL default value for this project is 10,000 nits**

### Device Management

- Global device state is maintained in `decklink_control.py` for API usage
- Device enumeration happens at initialization
- Pixel format auto-selection prefers 12-bit RGB formats
- Multiple devices can be targeted by index

## Testing

- Unit tests are in `tests/` directory
- Focus on pattern generation and pixel format conversion
- Use pytest framework for test execution

## Common Issues

- **Library Loading**: Ensure `libdecklink.dylib` is built and in correct
  location
- **Device Access**: Requires BMD Desktop Video drivers and proper device
  connection
- **Pixel Format**: Some formats may not be supported by all devices
- **HDR Metadata**: Complete metadata structure required for proper HDR output

## Dependencies

- Python 3.11+ with numpy, FastAPI, pydantic
- Blackmagic Design Desktop Video drivers
- Blackmagic Design DeckLink SDK 14.4
- clang++ with C++20 support (macOS)
- UV package manager for Python environment

## Claude Code Guidelines

- **Refactoring Workflow**:
  - Always make refactor suggestions using edit or multi edit tools so I can see
    the changes in my diff browser
  - Only use code snippets in the chat when I ask for an example or a clarifying
    question
  - When asked for refactor suggestions, first describe suggestions briefly with
    minimal code in the chat
  - Wait for explicit confirmation before using edit or multi edit tools to
    implement refactoring
