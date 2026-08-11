"""
Deprecated shim for ``display_patterns.charts``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts`` imports keep working for one
release cycle. Import from ``display_patterns.charts`` instead.
"""

import warnings

from display_patterns.charts import (
    ChartLayout,
    ColorValue,
    Patch,
    TiffMetadata,
    load_chart_tiff,
    render_chart,
    write_chart_tiff,
    xyz_to_display_rgb,
)

warnings.warn(
    "bmd_sg.charts is deprecated; import display_patterns.charts instead",
    DeprecationWarning,
    stacklevel=2,
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
