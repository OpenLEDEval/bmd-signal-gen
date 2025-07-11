# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project is a cross-platform BMD (Blackmagic Design) signal generator that outputs test patterns via DeckLink devices. It consists of:

- **C++ core**: Low-level DeckLink SDK wrapper with pixel format conversion (`cpp/`)
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

### Running the Application

**CLI Usage:**
```bash
bmd_signal_gen <r> <g> <b> [--duration 5] [--device 0]
```

**REST API:**
```bash
uvicorn bmd_sg.api:app
```

**Tests:**
```bash
python -m pytest tests/
```

## Code Architecture

### Core Components

1. **DeckLink C++ Wrapper** (`cpp/decklink_wrapper.cpp`):
   - Direct interface to BMD SDK
   - Handles device enumeration, pixel format management
   - Frame scheduling and HDR metadata injection

2. **Pixel Format Handling** (`cpp/pixel_packing.cpp`):
   - Converts RGB data to DeckLink-specific pixel formats
   - Supports 8/10/12-bit depths and various color spaces
   - Handles endianness and packing requirements

3. **Python Interface** (`bmd_sg/decklink/bmd_decklink.py`):
   - ctypes wrapper for C++ library
   - Provides `BMDDeckLink` class for high-level operations
   - Manages HDR metadata structures

4. **Pattern Generation** (`bmd_sg/patterns.py`):
   - Creates test patterns (solid, two-color, four-color)
   - Handles ROI (Region of Interest) specification
   - Supports various bit depths and color spaces

5. **Device Control** (`bmd_sg/decklink_control.py`):
   - Orchestrates pattern generation and device output
   - Manages global device state for API usage
   - Handles HDR metadata application

### Key Data Flow

1. Pattern generation creates numpy arrays with RGB values
2. Arrays are passed to DeckLink wrapper via ctypes
3. C++ code converts to appropriate pixel format
4. DeckLink SDK handles hardware output with HDR metadata

## Development Guidelines

### Critical Standards (from .cursor/rules/coding-standards.mdc)

- **DRY Principle**: Eliminate duplicate logic, especially switch/case statements for pixel formats
- **Centralized Logic**: Use helpers/utilities rather than repeating validation/conversion code
- **Refactor Immediately**: Don't defer deduplication - fix patterns when found
- **All Languages**: Apply DRY to C++, Python, and build scripts

### HDR Metadata Handling

The project supports complete HDR metadata with:
- EOTF (Electro-Optical Transfer Function) specification
- Display primaries (Rec2020 by default)
- Mastering display luminance values
- MaxCLL/MaxFALL content light levels

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

- **Library Loading**: Ensure `libdecklink.dylib` is built and in correct location
- **Device Access**: Requires BMD Desktop Video drivers and proper device connection
- **Pixel Format**: Some formats may not be supported by all devices
- **HDR Metadata**: Complete metadata structure required for proper HDR output

## Dependencies

- Python 3.11+ with numpy, FastAPI, pydantic
- Blackmagic Design Desktop Video drivers
- Blackmagic Design DeckLink SDK 14.4
- clang++ with C++20 support (macOS)
- UV package manager for Python environment