# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial test suite infrastructure with pytest fixtures
- PEP 561 `py.typed` marker for type checker support

### Fixed
- Typo in pyright configuration (`reportUnnecessaryTypeIgnoreComment`)

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
