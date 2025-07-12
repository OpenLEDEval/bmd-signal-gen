# Developer Documentation

This document outlines development standards, coding practices, and contribution guidelines for the BMD Signal Generator project.

## Project Overview

The BMD Signal Generator is a cross-platform tool for generating test patterns via Blackmagic Design DeckLink devices. It consists of multiple components:

- **C++ Core**: Low-level DeckLink SDK wrapper
- **Python Library**: High-level interface with ctypes bindings
- **REST API**: FastAPI-based HTTP interface
- **CLI Tool**: Command-line interface for direct usage

## Code Quality Management with Invoke

This project uses [Invoke](https://www.pyinvoke.org/) for task automation and code quality maintenance. Invoke provides a simple way to run common development tasks like linting, formatting, and testing.

### Available Tasks

Run `invoke --list` to see all available tasks:

```bash
invoke --list
```

### Core Quality Commands

**Main workflow commands:**
```bash
invoke check           # Run all checks (lint, format check, typecheck)
invoke fix             # Auto-fix linting issues and format code
```

**Individual quality tools:**
```bash
invoke lint            # Run ruff linting (read-only)
invoke lint --fix      # Run ruff linting with auto-fix
invoke format          # Format code with ruff
invoke format --check  # Check formatting without making changes
invoke typecheck       # Run pyright type checking
```

**Development workflow:**
```bash
invoke dev             # Quick development cycle: fix issues + run tests
invoke test            # Run pytest test suite
invoke clean           # Clean up cache files and build artifacts
invoke build           # Build C++ library and Python package (runs clean first)
```

### Typical Development Workflow

**Before starting work:**
```bash
invoke clean           # Clean up any stale files
invoke build           # Ensure fresh build
```

**During development:**
```bash
invoke fix             # Auto-fix issues and format code
invoke test            # Run tests to verify changes
```

**Before committing:**
```bash
invoke dev             # Runs fix + test in sequence
```

**For CI/CD validation:**
```bash
invoke check           # Read-only checks (matches CI pipeline)
```

### Task Details

- **`invoke check`**: Runs linting (read-only), format checking, and type checking
- **`invoke fix`**: Auto-fixes linting issues, formats code, then runs type checking
- **`invoke dev`**: Complete development cycle (fix + test)
- **`invoke build`**: Cleans first, then builds C++ library and Python package
- **`invoke clean`**: Removes cache files and the compiled library

### Tool Configuration

Code quality tools are configured in `pyproject.toml`:
- **Ruff**: Modern Python linter and formatter (replaces flake8, isort, black)
- **Pyright**: TypeScript-based Python type checker
- **Pytest**: Testing framework

All tools use consistent settings (line length: 88, Python 3.13+) and are optimized for the project's structure.

## Development Setup

### Prerequisites

- Python 3.11+ with UV package manager
- Blackmagic Design Desktop Video drivers
- Blackmagic Design DeckLink SDK 14.4
- clang++ with C++20 support (macOS)

### Environment Setup

```bash
# Install dependencies
uv sync

# Activate environment
source .venv/bin/activate

# Build C++ library
cd cpp && make clean && make && cd ..

# Run tests
python -m pytest tests/
```

## Documentation Standards

### Docstring Requirements

All Python code must use **Sphinx-compatible docstrings** following **NumPy documentation standards**. This ensures consistent, professional documentation that can be automatically processed by Sphinx for API documentation generation.

#### Module-Level Docstrings

Every Python module must have a comprehensive module-level docstring:

```python
"""
Brief one-line description of the module.

Longer description explaining the module's purpose, key functionality,
and how it fits into the overall project architecture.

The module includes:
- List of key components
- Major classes and functions
- Integration points with other modules

Examples
--------
Basic usage examples:

>>> from module import Class
>>> instance = Class()
>>> instance.method()

Notes
-----
Important notes about requirements, dependencies, or limitations.

See Also
--------
related.module : Description of related functionality
"""
```

#### Class Docstrings

All classes must have comprehensive docstrings using NumPy format:

```python
class ExampleClass:
    """
    Brief description of the class.
    
    Longer description explaining the class purpose, key functionality,
    and typical usage patterns.
    
    Parameters
    ----------
    param1 : type
        Description of the first parameter
    param2 : type, optional
        Description of optional parameter. Default is value.
    
    Attributes
    ----------
    attribute1 : type
        Description of public attribute
    attribute2 : type
        Description of another attribute
    
    Examples
    --------
    Basic usage:
    
    >>> obj = ExampleClass(param1="value")
    >>> result = obj.method()
    >>> print(result)
    Expected output
    
    Advanced usage:
    
    >>> with ExampleClass() as obj:
    ...     obj.configure()
    ...     obj.process()
    
    Raises
    ------
    ValueError
        When invalid parameters are provided
    RuntimeError
        When system resources are unavailable
    
    Notes
    -----
    Important implementation details, performance considerations,
    or compatibility notes.
    
    See Also
    --------
    RelatedClass : Description of related functionality
    """
```

#### Function/Method Docstrings

All public functions and methods must have NumPy-style docstrings:

```python
def example_function(param1, param2=None):
    """
    Brief description of what the function does.
    
    Longer description explaining the function's purpose, algorithm,
    or implementation details if relevant.
    
    Parameters
    ----------
    param1 : type
        Description of the first parameter
    param2 : type, optional
        Description of optional parameter. Default is None.
    
    Returns
    -------
    type
        Description of return value
    
    Raises
    ------
    ValueError
        When invalid input is provided
    TypeError
        When wrong parameter types are used
    
    Examples
    --------
    Basic usage:
    
    >>> result = example_function("input")
    >>> print(result)
    Expected output
    
    With optional parameters:
    
    >>> result = example_function("input", param2="optional")
    >>> print(result)
    Expected output
    
    Notes
    -----
    Performance considerations, algorithm complexity, or other
    important implementation details.
    
    See Also
    --------
    related_function : Description of related functionality
    """
```

#### Enum and Constants Documentation

Enums and module-level constants must be documented:

```python
class StatusType(Enum):
    """
    Enumeration of system status types.
    
    This enum defines the various states that the system can be in
    during operation, corresponding to different processing phases.
    
    Attributes
    ----------
    IDLE : int
        System is idle and ready for commands (0)
    PROCESSING : int
        System is actively processing data (1)
    ERROR : int
        System has encountered an error (2)
    
    Examples
    --------
    >>> status = StatusType.PROCESSING
    >>> print(status.value)
    1
    >>> print(status.name)
    PROCESSING
    """
    
    IDLE = 0
    PROCESSING = 1
    ERROR = 2

# Module constants
DEFAULT_TIMEOUT = 30.0
"""float: Default timeout value in seconds for network operations."""

MAX_RETRIES = 3
"""int: Maximum number of retry attempts for failed operations."""
```

### Docstring Requirements Summary

1. **All public modules, classes, functions, and methods** must have docstrings
2. **Use NumPy docstring format** with proper sections:
   - Parameters
   - Returns
   - Raises
   - Examples
   - Notes
   - See Also
3. **Include practical examples** that demonstrate real usage
4. **Document all parameters and return values** with types and descriptions
5. **List all exceptions** that can be raised
6. **Add cross-references** to related functionality
7. **Use consistent terminology** throughout the project

### Sphinx Integration

The project uses Sphinx for documentation generation. Docstrings are automatically processed to create API documentation. Key requirements:

- Use reStructuredText formatting within docstrings
- Cross-reference other modules using `:mod:`, `:class:`, `:func:` directives
- Include type hints in function signatures (preferred over docstring types)
- Use code blocks with proper syntax highlighting

### Documentation Testing

Docstring examples should be testable:

```python
def add_numbers(a, b):
    """
    Add two numbers together.
    
    Parameters
    ----------
    a : int or float
        First number
    b : int or float
        Second number
    
    Returns
    -------
    int or float
        Sum of a and b
    
    Examples
    --------
    >>> add_numbers(2, 3)
    5
    >>> add_numbers(2.5, 1.5)
    4.0
    """
    return a + b
```

Examples are validated using doctest or similar tools during CI/CD.

## Code Quality Standards

### General Principles

1. **DRY (Don't Repeat Yourself)**: Eliminate duplicate code through functions, classes, and modules
2. **Single Responsibility**: Each function/class should have one clear purpose
3. **Consistent Naming**: Use clear, descriptive names following Python conventions
4. **Error Handling**: Comprehensive error handling with meaningful messages
5. **Type Hints**: Use type hints for all function parameters and return values

### Python Standards

- Follow PEP 8 style guidelines
- Use type hints for all public APIs
- Maximum line length: 88 characters (Black formatter)
- Use dataclasses for simple data structures
- Prefer composition over inheritance

### C++ Standards

- Follow C++20 standards
- Use RAII for resource management
- Prefer smart pointers over raw pointers
- Use const correctness throughout
- Document public interfaces with Doxygen comments

## Testing Requirements

### Unit Tests

- All public functions must have unit tests
- Use pytest framework for Python tests
- Aim for >90% code coverage
- Mock external dependencies (DeckLink hardware, network calls)

### Integration Tests

- Test complete workflows end-to-end
- Include hardware-in-the-loop tests where possible
- Test error conditions and edge cases

### Documentation Tests

- All docstring examples must be testable
- Use doctest for simple examples
- Include examples in integration test suites

## Contributing Guidelines

### Pull Request Process

1. Create feature branch from `main`
2. Follow coding standards and add comprehensive tests
3. Update documentation including docstrings
4. Ensure all tests pass and coverage requirements are met
5. Submit PR with detailed description

### Code Review Requirements

- All code must be reviewed before merging
- Focus on correctness, performance, and maintainability
- Verify documentation quality and completeness
- Check for security considerations

### Release Process

1. Update version numbers in appropriate files
2. Update CHANGELOG.md with new features and fixes
3. Create release tag and GitHub release
4. Update documentation if needed

## Architecture Guidelines

### Component Separation

- Keep C++ layer minimal and focused on DeckLink SDK interaction
- Python layer handles business logic and API interfaces
- Clear separation between device control and pattern generation

### Error Handling

- Use exceptions for error conditions
- Provide meaningful error messages with context
- Log errors appropriately for debugging

### Performance Considerations

- Minimize memory allocations in video processing paths
- Use appropriate data structures for performance
- Profile critical paths and optimize as needed

## Security Guidelines

- Never commit secrets or API keys to the repository
- Validate all external inputs
- Use secure coding practices for C++ components
- Regular dependency updates and security scanning

## Additional Resources

- [NumPy Documentation Guide](https://numpydoc.readthedocs.io/en/latest/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [BMD DeckLink SDK Documentation](https://www.blackmagicdesign.com/support/download/af37b96d1b9a4a1cbe3f5d4e3b7c8cdb/Mac%20OS%20X)