# BMD Signal Generator Project Summary

Cross-platform BMD signal generator for Blackmagic Design DeckLink devices with HDR metadata support.

## Architecture

**Core Components**: C++ Core (`cpp/`) + Python Library (`bmd_sg/`) + CLI Tool + REST API  
**Technology**: Python 3.12+, ctypes, NumPy, Typer, DeckLink SDK 14.4, UV package manager

## Key Files & Components

### `/bmd_sg/decklink/`
**`bmd_decklink.py`**: Main SDK wrapper with `BMDDeckLink` class (RAII), `HDRMetadata` structure, pixel format enums, device enumeration. Default HDR: MaxCLL=10000 nits, PQ EOTF, Rec.2020 primaries  
**`decklink_types.py`**: Protocol definitions and type safety for ctypes wrapper

### `/bmd_sg/cli/`
**`main.py`**: Typer app with global parameters, rich help panels, command registration  
**`shared.py`**: Device setup workflow, pixel format auto-selection (12-bit RGB preferred), HDR metadata setup, color validation, centralized error handling  
**`commands/`**: Pattern commands (`checkerboard_commands.py`, `solid.py`, `device_details.py`)

### `/bmd_sg/image_generators/`
**`checkerboard.py`**: `PatternGenerator` class with ROI support, NumPy-based pattern generation, color expansion (1-4 colors), bit-depth validation, `ColorRangeError` exception

### `/bmd_sg/utilities/`
**`__init__.py`**: `suppress_cpp_output()` context manager for C++ library output redirection

## Key Features & Capabilities

**HDR Support**: Complete metadata structures (SMPTE ST 2086, CEA-861.3), standard color spaces (Rec.709/2020/DCI-P3/601), EOTF support (SDR/PQ/HLG), default MaxCLL=10,000 nits

**Pixel Format Support**: Auto-detection with preference system (12-bit RGB preferred), 8-bit to 12-bit YUV/RGB variants, format validation and bit-depth awareness

**Pattern Generation**: ROI-based rendering, optimized NumPy algorithms, color validation, flexible expansion (1-4 colors → checkerboard patterns)

**Device Management**: RAII pattern with automatic cleanup, context manager support, device enumeration, comprehensive error handling

## Development Standards

**Code Quality**: NumPy-style docstrings with examples, type hints throughout, DRY principle enforcement, centralized utilities
**Testing & Build**: UV package manager, invoke task automation, ruff/pyright quality checks, pre-commit hooks, C++ compilation integration
**Error Handling**: Specific exception types, hardware validation, SDK error translation with context

## Configuration Defaults

**Video**: 1920x1080, auto-select pixel format (12-bit RGB preferred), full frame ROI  
**HDR**: PQ EOTF, MaxCLL=10,000 cd/m², MaxFALL=400 cd/m², Rec.2020 primaries, D65 white point  
**Pattern Generation**: 12-bit with 100px border ROI, conservative white=2000/4095, black=0

## Dependencies & Implementation

**Core**: ctypes (C++ integration), numpy (array operations), typer (CLI), dataclasses (configuration)  
**External**: Desktop Video drivers, DeckLink SDK 14.4 headers, libdecklink.dylib, clang++ with C++20  
**Performance**: NumPy advanced indexing, contiguous memory layout, efficient ctypes buffers, minimal copying  
**Safety**: RAII/context managers, color validation, SDK signature verification, error context preservation  
**Extensibility**: Protocol-based type system, dataclass configuration, modular pattern generation, pluggable color spaces
