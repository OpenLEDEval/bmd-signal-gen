# DeckLink Module Development Guide

## Core Patterns

**Backend**: All device I/O goes through pydecklink (`pydecklink.Device`); do not add native code or ctypes here
**Protocol**: `DeckLinkOutput` defines the device surface; `BMDDeckLink` (hardware) and `MockBMDDeckLink` (no hardware) both satisfy it
**RAII Device Management**: Use `with BMDDeckLink(device_index=0) as device:` for automatic cleanup
**HDR Metadata**: Stored device-level via `set_hdr_metadata()`, attached per frame by the adapter. Defaults: EOTF=PQ(2), MaxCLL=10000 cd/m², Primaries=REC2020

## Key Functions

**Pixel Format**: Auto-selection prefers 12-bit RGB → 10-bit RGB → 10-bit YUV → 8-bit RGB; packing via `pydecklink.packing.pack`  
**Memory Management**: Use `np.ascontiguousarray()` for buffers, pre-allocate for performance, implement proper `close()`  
**Error Handling**: Translate pydecklink errors to `RuntimeError` with device context; keep `DeckLinkOutput` implementations exception-compatible

Core hardware interface - maintain compatibility and follow established safety patterns.
