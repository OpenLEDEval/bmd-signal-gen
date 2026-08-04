# bmd-signal-gen Specification

Declarative description of the system. Each section states what the
system does and why. See ROADMAP.md for work remaining.

## DeckLink Output Backend §spec:decklink-backend

*Status: complete*

### Problem

The DeckLink device layer was a private ctypes wrapper: `bmd_sg/decklink/
bmd_decklink.py` over `cpp/decklink_wrapper.cpp` and `cpp/pixel_packing.cpp`,
~2,850 lines. It was macOS-only, required an in-repo C++ build
(`libdecklink.dylib`) before anything ran, and duplicated
[pydecklink](https://github.com/Fuse-Technical-Group/pydecklink), which binds
the same SDK with nanobind, ships prebuilt wheels for macOS/Linux/Windows, and
already absorbed this repo's pixel packing and HDR metadata code as its
reference implementation.

### Backend

The device layer is pydecklink (>= 0.6.1, from PyPI). The repository contains
no C++ source and no native build step; a fresh clone runs after `uv sync`.

Why: one SDK binding maintained in one place. pydecklink 0.6.1 covers every
capability the ctypes wrapper provides — synchronous single-frame output,
pixel packing (`pydecklink.packing`), HDR10 static metadata
(`MutableFrame.set_hdr_metadata`), device enumeration, and per-device pixel
format queries.

### Device protocol

`bmd_sg.decklink` defines a `DeckLinkOutput` protocol matching the
established device surface:

- context manager; `close()` idempotent; `is_open`
- `start_playback()` / `stop_playback()`
- `get_supported_pixel_formats() -> list[PixelFormatType]`
- `pixel_format` property (get/set, `PixelFormatType`)
- `supports_hdr`
- `set_hdr_metadata(metadata)` — device-level, applies to all
  subsequent frames
- `display_frame(frame: np.ndarray)` — unpacked uint16, shape
  (height, width, 3), values in the pixel format's bit-depth range

`BMDDeckLink` implements the protocol over `pydecklink.Device`.
`MockBMDDeckLink` implements it with no hardware and backs `--mock-device`.

Why this surface: it is the existing `BMDDeckLink` API. Twelve call sites
(CLI, API server, examples) and the mock already code to it, so the swap is
confined to one adapter and callers do not change. pydecklink's own SPEC
names this integration path (§spec:test-pattern-generation): a narrow
protocol in signal-gen that either backend satisfies.

Why device-level HDR metadata: pydecklink attaches HDR metadata per frame
(the SDK model). Signal-gen emits static patterns where metadata never
varies frame-to-frame, so the adapter stores metadata once and attaches it
to every frame it builds. Callers keep the simpler device-level model.

### Semantics preserved from the ctypes wrapper

- Pixel packing: `display_frame` accepts unpacked uint16 RGB; the adapter
  packs to the device's pixel format via `pydecklink.packing.pack`.
- Display mode: HD 1080p30 default.
- Pixel format auto-selection: 12-bit RGB → 10-bit RGB → 10-bit YUV →
  8-bit, unchanged in `bmd_sg.cli.shared`.
- HDR defaults: EOTF=PQ, MaxCLL=10,000 nits, Rec.2020 primaries
  (project-specific, per CLAUDE.md).

### Out of scope

- Scheduled playback, capture, GPU pinned memory — pydecklink capabilities
  signal-gen does not use. Static pattern output remains synchronous
  single-frame.
- The FastAPI server's device management model (global state, enumeration
  at init) is unchanged.
