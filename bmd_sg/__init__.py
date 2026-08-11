"""
BMD Signal Generator package.

A cross-platform signal generator for Blackmagic Design DeckLink devices
that outputs test patterns with HDR metadata support.

Exports resolve lazily (PEP 562), so ``import bmd_sg`` loads neither the
DeckLink device layer nor the pattern library until a name is accessed.
"""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from display_patterns.image_generators.checkerboard import (
        ROI,
        ColorRangeError,
        PatternGenerator,
    )

    from bmd_sg.decklink.bmd_decklink import (
        BMDDeckLink,
        DeckLinkOutput,
        DecklinkSettings,
        EOTFType,
        GamutChromaticities,
        HDRMetadata,
        PixelFormatType,
    )

# name -> providing module. The runtime source of truth for the lazy
# exports; the TYPE_CHECKING block above mirrors it for static analysis.
_EXPORTS = {
    "BMDDeckLink": "bmd_sg.decklink.bmd_decklink",
    "DeckLinkOutput": "bmd_sg.decklink.bmd_decklink",
    "DecklinkSettings": "bmd_sg.decklink.bmd_decklink",
    "EOTFType": "bmd_sg.decklink.bmd_decklink",
    "GamutChromaticities": "bmd_sg.decklink.bmd_decklink",
    "HDRMetadata": "bmd_sg.decklink.bmd_decklink",
    "PixelFormatType": "bmd_sg.decklink.bmd_decklink",
    "ROI": "display_patterns.image_generators.checkerboard",
    "ColorRangeError": "display_patterns.image_generators.checkerboard",
    "PatternGenerator": "display_patterns.image_generators.checkerboard",
}

__all__ = [
    "ROI",
    "BMDDeckLink",
    "ColorRangeError",
    "DeckLinkOutput",
    "DecklinkSettings",
    "EOTFType",
    "GamutChromaticities",
    "HDRMetadata",
    "PatternGenerator",
    "PixelFormatType",
]


def __getattr__(name: str) -> object:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(_EXPORTS[name]), name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
