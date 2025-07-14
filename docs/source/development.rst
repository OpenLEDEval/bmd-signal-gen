Development Guide
=================

This guide covers how to contribute to the BMD Signal Generator project.

Development Setup
-----------------

1. **Clone the Repository**::

    git clone https://github.com/OpenLEDEval/bmd-signal-gen.git
    cd bmd-signal-gen

2. **Install Dependencies**::

    pip install uv
    uv sync --group dev --group docs

3. **Install Pre-commit Hooks**::

    uv run pre-commit install

4. **Build the Project**::

    uv run invoke build

Code Quality Tools
------------------

The project uses automated tools for code quality:

**Linting and Formatting**::

    uv run invoke lint        # Check code style
    uv run invoke lint --fix  # Auto-fix issues
    uv run invoke format      # Format code
    uv run invoke typecheck   # Type checking

**Complete Quality Check**::

    uv run invoke check       # Run all checks
    uv run invoke check-fix   # Fix and check all

**Development Workflow**::

    uv run invoke dev         # Quick cycle: fix + test

Testing
-------

Run the test suite::

    uv run invoke test
    # or directly
    uv run pytest tests/

**Test Organization:**
  * Unit tests in ``tests/``
  * Integration tests require DeckLink hardware
  * Mock external dependencies where possible

Documentation Standards
-----------------------

All code must follow strict documentation standards:

**Required Documentation:**
  * **All public modules** - Complete module docstrings
  * **All public classes** - Class docstrings with Parameters, Attributes, Examples
  * **All public functions** - Function docstrings with Parameters, Returns, Raises, Examples
  * **All constants/enums** - Brief descriptions

**Docstring Format:**
  * Use **NumPy-style docstrings** exclusively
  * Include practical examples with expected output
  * Document all exceptions that can be raised
  * Use consistent terminology throughout

**Example Function Docstring:**

.. code-block:: python

    def configure_pixel_format(device: BMDDeckLink, 
                             format_preference: str | None = None) -> PixelFormatType:
        """
        Configure and validate pixel format for DeckLink device.

        Automatically selects the best available pixel format from device 
        capabilities, with preference for higher bit depths and RGB formats.

        Parameters
        ----------
        device : BMDDeckLink
            Initialized DeckLink device context manager
        format_preference : str or None, optional
            Preferred format string (e.g., "12bit RGB"). If None, auto-selects
            based on device capabilities. Default is None.

        Returns
        -------
        PixelFormatType
            Selected pixel format enum value

        Raises
        ------
        ValueError
            If format_preference is specified but not supported by device
        RuntimeError
            If no supported pixel formats are available on device

        Examples
        --------
        Auto-select best format:

        >>> with BMDDeckLink(device_index=0) as device:
        ...     format_type = configure_pixel_format(device)
        ...     print(f"Selected: {format_type.name}")
        Selected: TWELVE_BIT_RGB

        Force specific format:

        >>> format_type = configure_pixel_format(device, "10bit YUV 422") 
        >>> print(format_type.name)
        TEN_BIT_YUV_422

        Notes
        -----
        Format preference order: 12-bit RGB > 10-bit RGB > 10-bit YUV 422 > others.
        Auto-selection ensures compatibility across different DeckLink models.

        See Also
        --------
        PixelFormatType : Available pixel format enumerations
        BMDDeckLink.get_supported_formats : Device format capabilities
        """

Coding Standards  
----------------

**General Principles:**
  * **DRY (Don't Repeat Yourself)** - Eliminate duplicate logic immediately
  * **Centralized Logic** - Use helpers/utilities rather than repeating code
  * **Type Annotations** - All functions must have complete type hints
  * **Error Handling** - Functions should raise exceptions rather than return None

**Code Style:**
  * Follow PEP 8 (enforced by ruff)
  * Maximum line length: 88 characters  
  * Use meaningful variable and function names
  * Prefer explicit over implicit

**Architecture Guidelines:**
  * Keep device management centralized in ``decklink_control.py``
  * Use dataclasses for configuration objects
  * Implement RAII patterns for resource management
  * Follow existing module organization patterns

Build System
-------------

The project uses a C++ core with Python bindings:

**C++ Component:**
  * Located in ``cpp/`` directory
  * Compiles to ``libdecklink.dylib`` (macOS) or equivalent
  * Uses DeckLink SDK 14.4
  * Handles low-level device operations and pixel format conversion

**Python Component:**
  * Uses ctypes for C++ library integration
  * High-level API in ``bmd_sg/`` package
  * CLI interface with Typer framework

**Build Process:**::

    uv run invoke build

This command:
  1. Cleans previous artifacts
  2. Compiles C++ library
  3. Builds Python package
  4. Validates build success

Contributing
------------

**Workflow:**
  1. Create feature branch from ``main``
  2. Make changes following coding standards
  3. Write tests for new functionality
  4. Update documentation as needed
  5. Run ``uv run invoke dev`` to test and fix issues
  6. Submit pull request with clear description

**Pull Request Guidelines:**
  * Include tests for new features
  * Update documentation for API changes
  * Ensure all quality checks pass
  * Provide clear commit messages
  * Reference related issues

**Code Review:**
  * All code is reviewed before merging
  * Focus on correctness, performance, and maintainability
  * Documentation quality is strictly enforced
  * No exceptions for incomplete documentation

Project Structure
-----------------

::

    bmd-signal-gen/
    ├── bmd_sg/                    # Main Python package
    │   ├── decklink/              # DeckLink SDK interface
    │   ├── image_generators/      # Pattern generation
    │   ├── cli/                   # Command-line interface
    │   └── utilities/             # Helper functions
    ├── cpp/                       # C++ core library
    ├── docs/                      # Sphinx documentation
    ├── tests/                     # Test suite
    ├── examples/                  # Usage examples
    ├── tasks.py                   # Invoke automation
    └── pyproject.toml             # Project configuration

Release Process
---------------

**Version Management:**
  * Use semantic versioning (MAJOR.MINOR.PATCH)
  * Update version in ``pyproject.toml``
  * Tag releases in git

**Release Checklist:**
  1. Run full test suite
  2. Update documentation
  3. Build and test package
  4. Create release notes
  5. Tag and push release
  6. Publish to PyPI (when ready)

Getting Help
------------

**Resources:**
  * Project documentation at https://bmd-signal-gen.readthedocs.io/
  * Issue tracker at https://github.com/OpenLEDEval/bmd-signal-gen/issues
  * DeckLink SDK documentation from Blackmagic Design

**Before Asking:**
  * Check existing documentation
  * Search closed issues
  * Verify hardware setup
  * Test with minimal examples