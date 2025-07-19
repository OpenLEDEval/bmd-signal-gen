# DeckLink Module Development Guide

## Core Patterns

**Ctypes Safety**: Always define function signatures with `argtypes` and `restype`
**RAII Device Management**: Use `with BMDDeckLink(device_index=0) as device:` for automatic cleanup
**HDR Metadata**: Complete metadata required. Defaults: EOTF=PQ(2), MaxCLL=10000 cd/m², Primaries=REC2020

## Key Functions

**Pixel Format**: Auto-selection prefers 12-bit RGB → 10-bit RGB → 10-bit YUV → 8-bit RGB  
**Memory Management**: Use `np.ascontiguousarray()` for buffers, pre-allocate for performance, implement proper `close()`  
**Error Handling**: Translate SDK errors to specific exceptions (`DeviceNotFoundError`, `PixelFormatError`, `DeckLinkError`)

## Threading
Use class-level locks for device exclusivity:
```python
_device_lock: ClassVar[threading.Lock] = threading.Lock()
_active_devices: ClassVar[dict[int, 'BMDDeckLink']] = {}
```

Core hardware interface - maintain compatibility and follow established safety patterns.