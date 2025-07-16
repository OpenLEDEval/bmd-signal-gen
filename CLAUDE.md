# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Homepage

Check metadata fields in @pyproject.toml for the project home page and author
information.

## Project Overview

This project is a cross-platform BMD (Blackmagic Design) signal generator that
outputs test patterns via DeckLink devices. It consists of:

- **C++ core**: Low-level DeckLink SDK wrapper with pixel format conversion
  (`cpp/`)
- **Python wrapper**: High-level interface via ctypes (`bmd_sg/`)
- **REST API**: FastAPI-based HTTP interface for pattern generation
- **CLI tool**: Command-line interface for direct pattern output

## Build Commands

Use the automated build system:

```bash
uv run invoke build
```

This builds `bmd_sg/decklink/libdecklink.dylib` and the Python package.

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
- Default HDR values do not reflect industry standards, but instead particular
  traits for disabling tone mapping or other automatic conversions in certain
  displays.

### Device Management

- Global device state is maintained in `decklink_control.py` for API usage
- Device enumeration happens at initialization
- Pixel format auto-selection prefers 12-bit RGB formats
- Multiple devices can be targeted by index

## Testing

Use `uv run invoke test` to run the test suite.

## Common Issues

- **Library Loading**: Ensure `libdecklink.dylib` is built and in correct
  location
- **Device Access**: Requires BMD Desktop Video drivers and proper device
  connection
- **Pixel Format**: Some formats may not be supported by all devices
- **HDR Metadata**: Complete metadata structure required for proper HDR output

## Dependencies

See DEVELOPERS.md for complete setup instructions including prerequisites and
SDK installation.

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
  - When refactoring, unless explicitly asked for do not preserve backwards
    compatibility. You can break the api as long as you make corrections
    throughout the code base. If it is too complicated, ask for help from the
    user.

### Code Quality Guidelines

- Always try to add a return type and type annotations to all functions
- Do not write functions that return `Optional` types or types that are
  sometimes None unless doing so adds functionality to the program. If a
  function cannot complete correctly, it should raise an error rather than
  returning None.

### Development Environment Management

- Use uv and uvx instead of using pip directly. This project uses uv to manage
  the development environment and development dependencies.
- **When running python snippets in this library, use `uv run python` instead of
  invoking python directly.**
- When using `uv run` for any tasks, make sure to change directories to the root
  directory. After running the tool, you may return to the previous directory if
  needed.
- **When checking the pre-commit configuration, use `uv run pre-commit` instead of invoking pre-commit directly**

### Project Testing

- Claude can run `python -m bmd_sg.cli.main` to test the cli for the project and
  user interface

### Module Maintenance Guidelines

- Where a module has an **all** declaration, make sure to keep it up to date by
  searching for usages of that module's public members. Ensure their usage and
  documentation are up to date with the latest changes.

### Development Tools

- AI Agents should use `uv run ai-developer-quality` to run quality checks while
  developing. Some of the checks modify files, so claude will need to re-read
  files.
- If the `ai-developer-quality` returns errors for code unrelated to the current
  project, agents may request to put code check comments around the violating
  code to bypass the check. Agents must always get explicit permission to do
  this and must remove the bypass after finishing their current project.

## Developer Guidelines

- Read @DEVELOPERS.md for additional guidance.
- Check @.memories/PROJECT_SUMMARY.md for additional guidance.
- You can search the .memories/DesktopVideoSDKManual.md files if needed for BMD
  SDK documentation during cpp development.

### Reference Example Paths

- Always use the path
  `@cpp/Blackmagic\ DeckLink\ SDK\ 14.4/Mac/Samples/SignalGenHDR` as known-good
  example code when working with the DeckLink SDK API