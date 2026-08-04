# bmd-signal-gen Roadmap

Derived from [SPEC.md](SPEC.md). Sections are in build-dependency order.

## DeckLink backend swap §spec:decklink-backend

- **adapter-over-pydecklink**: Reimplement `BMDDeckLink` as an adapter
  over `pydecklink.Device` behind the `DeckLinkOutput` protocol. Failing
  tests first: protocol conformance for both `BMDDeckLink` and
  `MockBMDDeckLink`, packing dispatch, device-level HDR metadata attached
  per frame. Call sites unchanged.
- **retire-ctypes-wrapper**: Delete the ctypes layer
  (`decklink_types.py`, the `ctypes.CDLL` loading in `bmd_decklink.py`)
  and all of `cpp/` — wrapper, pixel packing, CMake/Makefile, and the
  vendored DeckLink SDK 15.3 (pydecklink vendors its own headers; the
  SDK manual stays in `.memories/`). Remove native build steps from
  `tasks.py` and stale references in CLAUDE.md/README. Depends on
  adapter-over-pydecklink verified on hardware.
