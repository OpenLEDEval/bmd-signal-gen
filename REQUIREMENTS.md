# BMD Signal Generator - Requirements

## Core Functionality (P0)

**REQ-001**: The system MUST generate test patterns on Blackmagic Design DeckLink output devices.

**REQ-002**: The system MUST support solid color, 2-color checkerboard, and 4-color checkerboard patterns.

**REQ-003**: The system MUST support 8-bit, 10-bit, and 12-bit color depths.

**REQ-004**: The system MUST validate color values against the selected bit depth range.

**REQ-005**: The system MUST automatically detect and list available DeckLink devices.

## Interface Requirements (P0)

**REQ-006**: The system MUST provide a command-line interface for pattern generation.

**REQ-007**: The system MUST provide an HTTP REST API for remote control.

**REQ-008**: The API MUST accept both JSON and YAML input formats.

**REQ-009**: The system MUST return appropriate error messages for invalid inputs.

## Region of Interest (P1)

**REQ-010**: The system SHOULD support region of interest (ROI) functionality to display patterns within specified rectangular areas.

**REQ-011**: The system MUST validate ROI boundaries against image dimensions.

## HDR Support (P1)

**REQ-012**: The system MUST support HDR metadata including EOTF, MaxCLL, MaxFALL, and display mastering luminance.

**REQ-013**: The system SHOULD support PQ (HDR10) and HLG EOTF types.

**REQ-014**: The system MUST support Rec.2020 color primaries and custom chromaticity coordinates.

**REQ-015**: The system SHOULD allow disabling HDR metadata for SDR workflows.

## Hardware Compatibility (P1)

**REQ-016**: The system MUST support multiple DeckLink pixel formats with automatic format selection.

**REQ-017**: The system SHOULD prefer higher bit-depth formats when available.

**REQ-018**: The system MUST handle device initialization and cleanup properly.

## Performance & Reliability (P2)

**REQ-019**: The system SHOULD start pattern output within 2 seconds of command execution.

**REQ-020**: The system MUST handle device disconnection gracefully.

**REQ-021**: The API SHOULD support concurrent pattern requests (though hardware may limit this).

## Developer Experience (P2)

**REQ-022**: The system MUST provide clear error messages for missing hardware or drivers.

**REQ-023**: The system SHOULD log device capabilities and selected formats for debugging.

**REQ-024**: The system MAY provide verbose logging options for troubleshooting.

## Constraints & Limitations

**CONSTRAINT-001**: The system requires Blackmagic Design DeckLink hardware and drivers.

**CONSTRAINT-002**: Pattern generation is limited by hardware pixel format support.

**CONSTRAINT-003**: HDR metadata support depends on downstream display capabilities.

**CONSTRAINT-004**: Multiple concurrent outputs may conflict (hardware-dependent).

## Conflicting Requirements

- **REQ-017** (prefer higher bit-depth) vs **REQ-021** (concurrent requests) - higher bit-depth may reduce concurrent capability
- **REQ-019** (fast startup) vs **REQ-023** (verbose logging) - detailed logging may slow initialization
- **REQ-008** (flexible input formats) vs **REQ-009** (clear error messages) - format flexibility complicates error reporting