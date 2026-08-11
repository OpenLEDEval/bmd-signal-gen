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

## Pattern library §spec:pattern-library

*Status: in progress*

### Problem

`bmd_sg/image_generators/` and `bmd_sg/charts/` imported nothing from the
device layer: a generic pattern/chart library carried inside a DeckLink
tool. Other OpenLEDEval tools could not consume the math without DeckLink
baggage.

### Split

The modules and their tests moved verbatim to
[display-patterns](https://github.com/OpenLEDEval/display-patterns)
(import package `display_patterns`): `bmd_sg/image_generators/` →
`display_patterns.image_generators`, `bmd_sg/charts/` →
`display_patterns.charts`. The package is a numpy-only core taking a
caller-supplied array namespace, with `charts` and `io` extras supplying
the chart and file-export dependency stacks — their contents are
upstream's contract (`§spec:package-shape` there), not re-pinned here.

The API stays value-space agnostic: measurement drives exact integer code
values at a stated bit depth, so the library never rescales or quantizes
behind the caller. The frame-indexed rendering signature and the
temporal-alignment counter-panel catalog entry are specified in
display-patterns' own SPEC (`§spec:render-model`, `§spec:catalog` there);
this document does not re-spec them.

### Consumption

bmd-signal-gen depends on `display-patterns[charts,io]` as a git
dependency pinned to tag v0.1.0. PyPI publishing is deferred org-wide
pending the org rename/confirmation, tracked in display-patterns' roadmap
(`§road:first-release` there). Consequence: bmd-signal-gen cannot itself
publish to PyPI while carrying a git dependency — acceptable, it is not
published today.

### Deprecation shims

Every previously importable module path under `bmd_sg.image_generators`
and `bmd_sg.charts` keeps working for one release cycle as a re-export
shim: module-level `DeprecationWarning`, explicit re-exports, `__all__`
preserved. Importing a nested shim warns once per shim package on the
path (parent, then leaf) — the accepted cost of per-module shims. The
`bmd_sg.charts` shim mirrors upstream's lazy loading, so no shim import
drags in the chart dependency stack. The root package's `ROI`,
`PatternGenerator`, and `ColorRangeError` re-exports are permanent
façade surface, not shims: they resolve silently and stay after
§road:remove-shims. CLI, API server, and examples import
`display_patterns.*` directly. Shim removal is scheduled
(§road:remove-shims).
