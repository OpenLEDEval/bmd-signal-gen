"""
Deprecated shim for ``display_patterns.charts``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts`` imports keep working for one
release cycle. Import from ``display_patterns.charts`` instead.

Mirrors upstream's lazy loading: only the numpy-only ``color_types``
names load eagerly, so importing this shim (or any submodule shim) does
not drag in colour-science, Pillow, or tifffile.
"""

import importlib
from typing import TYPE_CHECKING

from display_patterns.charts import ChartLayout, ColorValue, Patch

from bmd_sg.utilities import warn_moved

if TYPE_CHECKING:
    from display_patterns.charts import (
        TiffMetadata,
        load_chart_tiff,
        render_chart,
        write_chart_tiff,
        xyz_to_display_rgb,
    )

warn_moved(__name__)

# Heavy names resolve through upstream's own lazy facade on first access.
_LAZY_EXPORTS = (
    "TiffMetadata",
    "load_chart_tiff",
    "render_chart",
    "write_chart_tiff",
    "xyz_to_display_rgb",
)

__all__ = [
    "ChartLayout",
    "ColorValue",
    "Patch",
    "TiffMetadata",
    "load_chart_tiff",
    "render_chart",
    "write_chart_tiff",
    "xyz_to_display_rgb",
]


def __getattr__(name: str) -> object:
    if name in _LAZY_EXPORTS:
        return getattr(importlib.import_module("display_patterns.charts"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
