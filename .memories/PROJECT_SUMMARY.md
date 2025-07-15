# BMD Signal Generator Project Summary

_Generated from commit: 8180de76df23a977f2d8912f8aef913999b3ede4_

This is a context file for AI contributors. Do not mix requirements or model
specific instructions into this file. It should only summarize the functionality
and locations of key places in the project.

## Overview

Cross-platform BMD signal generator for Blackmagic Design DeckLink devices with
HDR metadata support. Outputs test patterns via professional video hardware.

## Architecture

### Core Components

- **C++ Core** (`cpp/`): Low-level DeckLink SDK wrapper with pixel format
  conversion
- **Python Library** (`bmd_sg/`): High-level interface via ctypes bindings
- **CLI Tool**: Command-line interface for direct pattern output
- **REST API**: FastAPI-based HTTP interface for pattern generation

### Technology Stack

- Python 3.13+ with ctypes for C++ library integration
- NumPy for image/pattern generation and array operations
- Typer for CLI framework with rich help panels
- Blackmagic Design DeckLink SDK 14.4
- UV package manager for dependency management

## Project Structure Analysis

### `/bmd_sg/` - Main Python Package

#### Core DeckLink Interface (`/bmd_sg/decklink/`)

**`bmd_decklink.py`** (1359 lines) - Main DeckLink SDK wrapper

- `BMDDeckLink` class: RAII wrapper for device management with context manager
  support
- `HDRMetadata` ctypes structure: Complete HDR metadata (EOTF, primaries,
  mastering display, content light levels)
- `Gamut_Chromaticities`: Color space primaries (Rec.709, Rec.2020, DCI-P3,
  Rec.601)
- `PixelFormatType` enum: Format types with bit depths and SDK codes (8-bit to
  12-bit, YUV/RGB)
- `EOTFType` enum: Transfer functions (SDR, PQ/HDR10, HLG)
- `DecklinkSettings` dataclass: Unified configuration (device, resolution, ROI,
  HDR params)
- Device enumeration, pixel format management, HDR metadata handling
- Automatic function signature configuration for ctypes safety
- Default HDR values: MaxCLL=10000 nits, Rec.2020 primaries, PQ EOTF

**`decklink_types.py`** (128 lines) - Type definitions and protocols

- `DecklinkSDKProtocol`: Complete protocol definition for ctypes wrapper
- Type safety for all SDK functions (device mgmt, pixel formats, HDR, frame
  operations)

#### CLI Interface (`/bmd_sg/cli/`)

**`main.py`** (213 lines) - Main CLI application with global device
configuration

- Typer app with comprehensive global parameters (device, pixel format,
  resolution, ROI, HDR)
- Rich help panels for organized options
- Global callback stores settings in context for subcommands
- Command registration for pattern generators and device details
- HDR defaults: PQ EOTF, 10000 nits MaxCLL, Rec.2020 primaries

**`shared.py`** (537 lines) - Common CLI utilities and device management

- `initialize_device()`: Complete device setup workflow (discovery, create,
  configure, start)
- `configure_pixel_format()`: Auto-selection with preference order (12-bit RGB >
  10-bit RGB > 10-bit YUV)
- `configure_hdr_metadata()`: HDR metadata setup with complete structure
- `validate_color()`: Bit-depth aware color validation (8/10/12-bit ranges)
- `setup_tools_from_context()`: Main entry point for pattern commands
- Device enumeration, validation, pattern generator creation
- Centralized error handling and logging

**CLI Commands** (`/bmd_sg/cli/commands/`)

**`checkerboard_commands.py`** (344 lines) - Multi-color checkerboard patterns

- `checkerboard2_command()`: Two-color alternating checkerboard
- `checkerboard3_command()`: Three-color checkerboard with custom mapping
- `checkerboard4_command()`: Four-color true 2x2 checkerboard
- Comprehensive documentation with examples and color value ranges
- Pattern-specific parameters with device inheritance from global context

**`solid.py`** (98 lines) - Solid color pattern generation

- Single solid color across entire frame or ROI
- Color validation and duration control
- Ideal for display uniformity testing and luminance measurement

**`device_details.py`** (98 lines) - Device inspection and capabilities

- System information (SDK/driver versions)
- Device enumeration with supported pixel formats and bit depths
- HDR capability detection per device
- Safe device access with context managers

#### Pattern Generation (`/bmd_sg/image_generators/`)

**`checkerboard.py`** (356 lines) - Core pattern generation engine

- `PatternGenerator` class: Bit-depth aware pattern creation with ROI support
- `ROI` dataclass: Region of interest definition with coordinate management
- `_draw_checkerboard_pattern()`: Optimized NumPy-based checkerboard generation
  using advanced indexing
- Color expansion logic: 1-4 colors mapped to 4-color checkerboard patterns
- Color validation against bit depth constraints (8-bit: 0-255, 12-bit: 0-4095)
- Default generator: 1080p 12-bit with 100px border ROI (1720x880 active)
- `ColorRangeError`: Custom exception for color validation failures

#### Utilities (`/bmd_sg/utilities/`)

**`__init__.py`** (61 lines) - System utilities

- `suppress_cpp_output()`: Context manager for C++ library output suppression
- File descriptor redirection for clean operation

## Key Features & Capabilities

### HDR Support

- Complete HDR metadata structures (SMPTE ST 2086, CEA-861.3)
- Standard color spaces: Rec.709, Rec.2020, DCI-P3, Rec.601
- EOTF support: SDR, PQ (HDR10), HLG (broadcast HDR)
- Configurable mastering display and content light levels
- Default MaxCLL: 10,000 nits (project-specific high value)

### Pixel Format Support

- Auto-detection and format preference system
- 8-bit to 12-bit support with YUV/RGB variants
- Format validation and bit-depth awareness
- SDK format code mapping and parsing

### Pattern Generation

- ROI-based pattern rendering for targeted testing
- Optimized NumPy algorithms for real-time generation
- Color validation against device bit depth
- Flexible color expansion (1-4 colors → checkerboard patterns)

### Device Management

- RAII pattern with automatic resource cleanup
- Context manager support for safe device access
- Device enumeration and capability detection
- Error handling with detailed diagnostics

## Development Standards

### Code Quality

- Comprehensive NumPy-style docstrings with examples
- Type hints throughout codebase
- DRY principle enforcement - no duplicate logic
- Centralized validation and configuration utilities

### Testing & Build

- UV package manager with invoke task automation
- Automated code quality: ruff (linting/formatting), pyright (type checking)
- Pre-commit hooks for code standards enforcement
- C++ library compilation with make integration

### Error Handling

- Comprehensive exception types with detailed messages
- Hardware validation and graceful fallbacks
- SDK error code translation and context

## Configuration Defaults

### Video

- Resolution: 1920x1080 (Full HD)
- Pixel Format: Auto-select (prefers 12-bit RGB)
- ROI: Full frame (configurable)

### HDR

- EOTF: PQ (Perceptual Quantizer for HDR10)
- MaxCLL: 10,000 cd/m² (project-specific high luminance)
- MaxFALL: 400 cd/m²
- Primaries: Rec.2020 (Ultra HD standard)
- White Point: D65 (0.3127, 0.3290)

### Pattern Generation

- Default: 12-bit with 100px border ROI
- Conservative white level: 2000/4095 ≈ 49% for HDR displays
- Black level: 0 (minimum luminance)

## Dependencies & Integration

### Core Dependencies

- ctypes (stdlib): C++ library integration
- numpy: Array operations and pattern generation
- typer: CLI framework with rich features
- dataclasses: Configuration management

### External Requirements

- Blackmagic Design Desktop Video drivers
- DeckLink SDK 14.4 headers
- Compiled libdecklink.dylib (built from cpp/)
- clang++ with C++20 support

## Notable Implementation Details

### Performance Optimizations

- NumPy advanced indexing for pattern generation (no Python loops)
- Contiguous memory layout for frame data transfer
- Efficient ctypes buffer management
- Minimal array copying with in-place operations

### Safety Features

- Automatic device cleanup with RAII and context managers
- Color value validation before hardware access
- SDK function signature verification
- Error propagation with context preservation

### Extensibility

- Protocol-based type system for SDK wrapper
- Dataclass configuration for easy extension
- Modular pattern generation with ROI abstraction
- Pluggable color space and EOTF definitions

This summary captures the essential architecture, functionality, and
implementation details for future development reference.
