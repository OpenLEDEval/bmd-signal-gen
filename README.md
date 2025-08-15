# BMD Signal Generator

> **⚠️ AI-Generated Documentation Notice**  
> Much of this project's documentation was generated using AI assistance. The
> project and its documentation may contain bugs, missing features, or may not
> work correctly on certain hardware or operating system configurations. The
> authors primarily develop on macOS but have made their best effort to make the
> software cross-platform. If you encounter issues or have questions, please
> start a
> [GitHub Discussion](https://github.com/OpenLEDEval/bmd-signal-gen/discussions).

A cross-platform BMD signal generator for Blackmagic Design DeckLink devices
that outputs test patterns with comprehensive HDR metadata support. This project
enables deterministic test pattern generation that is not affected by OS or GPU
variability, making it ideal for professional video testing and display
calibration.

Recommended output interfaces include the
[UltraStudio Monitor 3G](https://www.blackmagicdesign.com/products/ultrastudio/techspecs/W-DLUS-13)
and
[UltraStudio 4K Mini](https://www.blackmagicdesign.com/products/ultrastudio/techspecs/W-DLUS-11),
both capable of full 12-bit RGB output at 1080p30.

## Features

- **HDR Support**: Complete HDR metadata with SMPTE ST 2086 and CEA-861.3
  compliance
- **Multiple Pixel Formats**: Auto-detection and support for 8-bit to 12-bit
  YUV/RGB formats
- **Pattern Generation**: Solid colors and multi-color checkerboard patterns
  with ROI support
- **Device Management**: Automatic device enumeration and capability detection
- **Color Spaces**: Rec.709, Rec.2020, DCI-P3, and Rec.601 primaries support
- **EOTF Support**: SDR, PQ (HDR10), and HLG transfer functions
- **CLI Interface**: Rich command-line interface with organized help panels
- **REST API**: FastAPI-based HTTP interface for pattern generation

## Quick Start

### Prerequisites

- **macOS** (tested on macOS 15.5) or Windows
- **Blackmagic Design Desktop Video drivers** (latest version)
- **Blackmagic Design DeckLink SDK 14.4**
- **Python 3.13+**
- **UV package manager**
  ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **clang++** with C++20 support (macOS) or equivalent C++ compiler

### Installation

1. **Get the DeckLink SDK** (see [DEVELOPERS.md](DEVELOPERS.md) for detailed
   instructions):

   ```bash
   mkdir -p cpp/include/DeckLinkAPI
   cp /path/to/decklink-sdk/Mac/include/* cpp/include/DeckLinkAPI/
   ```

2. **Install dependencies and build**:

   ```bash
   uv sync
   uv run invoke build
   ```

3. **Verify installation**:
   ```bash
   uv run bmd-signal-gen --help
   ```

## Usage

### CLI Interface

The CLI provides a comprehensive interface with global device configuration and
pattern-specific commands:

```bash
# Show available devices and their capabilities
uv run bmd-signal-gen device-details

# Generate solid white pattern for 10 seconds
uv run bmd-signal-gen solid 4095 4095 4095 --duration 10

# Generate two-color checkerboard with custom colors
uv run bmd-signal-gen pat2 4095 0 0 --color2 0 4095 0 --duration 5

# Generate four-color checkerboard with HDR settings
uv run bmd-signal-gen --device 1 --eotf HLG --max-cll 4000 pat4 4095 0 0 --color2 0 4095 0 --color3 0 0 4095 --color4 4095 4095 4095
```

### Global Options

- `--device`, `-d`: Device index (default: 0)
- `--pixel-format`, `-p`: Pixel format (auto-select if not specified)
- `--width`, `--height`: Resolution (default: 1920x1080)
- `--roi-x`, `--roi-y`, `--roi-width`, `--roi-height`: Region of interest
- `--eotf`: EOTF type - SDR, PQ, HLG (default: PQ)
- `--max-cll`: Maximum Content Light Level in cd/m² (default: 10000)
- `--max-fall`: Maximum Frame Average Light Level in cd/m² (default: 80)
- `--no-hdr`: Disable HDR metadata output

### Available Commands

- **`solid`**: Single solid color patterns
- **`pat2`**: Two-color checkerboard patterns
- **`pat3`**: Three-color checkerboard patterns
- **`pat4`**: Four-color checkerboard patterns
- **`device-details`**: Show device information and capabilities

### Color Value Ranges

Color values depend on the device's pixel format:

- **12-bit**: 0-4095 (default, recommended)
- **10-bit**: 0-1023
- **8-bit**: 0-255

**Note that bmd-signal-gen does not enforce "video" or limited range checking, nor do any conversion from full-range to limited or vice-versa. Please handle this manually as necessary in the design and configuration of your patterns and pixel format selection**

## Project Structure

```
bmd-signal-gen/
├── bmd_sg/                           # Main Python package
│   ├── cli/                          # Command-line interface
│   │   ├── main.py                   # Main CLI application
│   │   ├── shared.py                 # Common utilities and device management
│   │   └── commands/                 # Pattern-specific commands
│   ├── decklink/                     # DeckLink SDK wrapper
│   │   ├── bmd_decklink.py           # Main wrapper with HDR support
│   │   ├── decklink_types.py         # Type definitions and protocols
│   │   └── libdecklink.dylib         # Compiled C++ library
│   ├── image_generators/             # Pattern generation
│   │   └── checkerboard.py           # Checkerboard pattern generator
│   └── utilities/                    # System utilities
├── cpp/                              # C++ DeckLink SDK wrapper
│   ├── include/DeckLinkAPI/          # DeckLink SDK headers
│   ├── decklink_wrapper.cpp          # C++ implementation
│   └── Makefile                      # Build configuration
├── tests/                            # Unit tests
├── tasks.py                          # Invoke task automation
├── DEVELOPERS.md                     # Development setup guide
└── CLAUDE.md                         # AI development guidelines
```

## Development

### Build Commands

```bash
uv run invoke build     # Build C++ library and Python package
uv run invoke check     # Run all checks (lint, format, typecheck)
uv run invoke fix       # Auto-fix issues and format code
uv run invoke test      # Run pytest test suite
uv run invoke dev       # Quick cycle: fix + test
```

### Code Quality

The project maintains high code quality standards:

- **Ruff** for linting and formatting
- **Pyright** for type checking
- **Pre-commit hooks** for automated quality checks
- **NumPy-style docstrings** with comprehensive examples
- **Type hints** throughout the codebase

## HDR Configuration

Default HDR settings follow standards:

- **EOTF**: PQ (Perceptual Quantizer for HDR10)
- **MaxCLL**: 10,000 cd/m² (project-specific high luminance)
- **MaxFALL**: 400 cd/m²
- **Color Primaries**: Rec.2020 (Ultra HD standard)
- **White Point**: D65 (0.3127, 0.3290)

## Contributing

See [DEVELOPERS.md](DEVELOPERS.md) for complete development setup instructions
and coding standards.

## License

See [LICENSE](LICENSE)
