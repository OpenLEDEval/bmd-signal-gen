# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial test suite infrastructure with pytest fixtures
- PEP 561 `py.typed` marker for type checker support
- `DeckLinkOutput` protocol describing the device output surface; satisfied
  by both `BMDDeckLink` (hardware) and `MockBMDDeckLink` (`--mock-device`)
- SPEC.md and ROADMAP.md governance documents

### Changed
- DeckLink device layer now uses [pydecklink](https://github.com/Fuse-Technical-Group/pydecklink)
  (>= 0.6.1, PyPI) instead of the private ctypes wrapper. 12-bit RGB (R12L),
  r210, and BGRA packing verified byte-identical to the retired
  implementation; HDR metadata signalling verified on the wire
- `HDRMetadata` and `GamutChromaticities` are plain Python classes
  (identical constructors and attributes; no longer `ctypes.Structure`)
- `get_decklink_sdk_version()` reports the driver API version (pydecklink
  links the DeckLink SDK dynamically)

### Removed
- `cpp/` tree: ctypes wrapper, pixel packing, CMake build, and vendored
  DeckLink SDK 15.3 — a fresh clone runs after `uv sync` with no native build
- `bmd_sg/decklink/decklink_types.py` and `libdecklink.dylib` packaging
- CMake/LLVM toolchain setup tasks from `tasks.py`

### Fixed
- Typo in pyright configuration (`reportUnnecessaryTypeIgnoreComment`)
- ARGB output byte order: the retired C++ packer emitted RGBA memory order
  for `bmdFormat8BitARGB`; pydecklink packs A,R,G,B per the SDK. The broken
  path was unreachable from the CLI (8-bit formats are filtered out)

## [0.1.0] - 2025-07-14

### Added
- Cross-platform BMD signal generator for Blackmagic Design DeckLink devices
- HDR metadata support with SMPTE ST 2086 and CEA-861.3 compliance
- Multiple pixel formats: 8-bit to 12-bit YUV/RGB formats
- Pattern generation: Solid colors and multi-color checkerboard patterns with ROI support
- Device management with automatic enumeration and capability detection
- Color spaces: Rec.709, Rec.2020, DCI-P3, and Rec.601 primaries support
- EOTF support: SDR, PQ (HDR10), and HLG transfer functions
- Rich CLI interface with organized help panels
- FastAPI-based REST API for pattern generation
- Mock device support for development and testing without hardware
- Comprehensive NumPy-style documentation

[Unreleased]: https://github.com/OpenLEDEval/bmd-signal-gen/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/OpenLEDEval/bmd-signal-gen/releases/tag/v0.1.0
