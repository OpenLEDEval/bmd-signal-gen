# BMD Signal Generator

This project enables the generation of test patterns in a cross-platform, highly
deterministic way that is not perturbed by OS or GPU variability. It does this
by providing C++ and Python wrappers for the BlackMagic Design Decklink API.
Recommended output interfaces are the
[UltraStudio Monitor 3G](https://www.blackmagicdesign.com/products/ultrastudio/techspecs/W-DLUS-13)
and the
[UltraStudio 4K Mini](https://www.blackmagicdesign.com/products/ultrastudio/techspecs/W-DLUS-11).
Both interfaces should be able to output full 12-bit RGB at 1080p30.

The project includes a basic command-line tool to illustrate how to use the
wrapper.

## Overview

This project allows you to:

- Enumerate and select connected DeckLink devices
- Query supported pixel formats for each device
- Output solid and checkerboard RGB color test patterns to DeckLink devices
- Control output duration and device selection

## Requirements

- macOS (tested on macOS 15.5) or presumably Windows
- Blackmagic Design Desktop Video drivers (tested with 14.5)
- Blackmagic Design DeckLink SDK (tested with 14.4)
- Python 3.11+ (for Python interface)
- clang++ (c++20 or newer) compiler

## Project Structure

```
bmd-signal-gen/
├── bmd_signal_gen.py             # Command-line application
├── cpp/                          # BMD DeckLink API C++ wrapper
│   ├── decklink_wrapper.h        # C API header
│   ├── decklink_wrapper.cpp      # C API implementation
│   ├── pixel_packing.h           # Pixel format conversion utilities
│   ├── pixel_packing.cpp         # Pixel format conversion implementation
│   ├── PIXEL_PACKING_DOCUMENTATION.md  # Documentation for pixel packing
│   ├── Makefile                  # Build configuration for C++ library
│   └── Blackmagic DeckLink SDK 14.4/  # Blackmagic Design SDK
├── lib/                          # Python interface and built library artifact
│   ├── bmd_decklink.py           # Python ctypes wrapper
│   └── libdecklink.dylib         # Built dynamic library (macOS)
├── src/                          # Python package source code
│   └── bmdsignalgen/             # Main Python package
│       └── patterns.py           # Pattern generation classes and utilities
├── tests/                        # Unit tests
│   └── test_patterns.py          # Tests for pattern generation
├── pyproject.toml                # UV project configuration
├── uv.lock                       # UV dependency lock file
└── README.md                     # This file
```

## Building

### Prerequisites

1. Install the Blackmagic Design Desktop Video driver
2. Install the Blackmagic Design DeckLink SDK
3. Ensure the SDK is located at `cpp/Blackmagic DeckLink SDK 14.4/` relative to
   the project root
4. Install Python 3.11+ and UV package manager

### Build the C++ Library

```bash
cd cpp && make clean && make && cd ..
```

This creates `bmd_sg/decklink/libdecklink.dylib` - a dynamic library that
provides the C API for DeckLink device control.

### Python Environment Setup

The project uses UV for Python dependency management:

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync
```

## Usage

### Python Command-Line Interface

The easiest way to use this project is through the Python command-line
interface. After installing / `uv sync` you can activate your `.venv` by calling

```sh
source .venv/bin/activate
```

or one of the other activate scripts depending on your choice of shell (for
example, `source .venv/bin/activate.fish`)

```bash
bmd_signal_gen <r> <g> <b> [options]
```

#### Examples

CLI usage: output 12-bit red color for 5 seconds:

```bash
bmd_signal_gen 4095 0 0
```

# REST API (default host 127.0.0.1 port 8000)

```bash
uvicorn bmd_signal_gen:app
```

#### Command-Line Options

- `r`, `g`, `b`: Red, green, blue components (0-4095)
- `--duration`, `-d`: Output duration in seconds (default: 5.0)
- `--device`: Device index to use (default: 0)

## Contributing

See CONTRIBUTING.md

## License

See LICENSE
