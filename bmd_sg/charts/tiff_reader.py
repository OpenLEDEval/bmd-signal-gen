"""
Deprecated shim for ``display_patterns.charts.tiff_reader``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.tiff_reader`` imports keep
working for one release cycle. Import from
``display_patterns.charts.tiff_reader`` instead.
"""

from display_patterns.charts.tiff_reader import TiffMetadata, load_chart_tiff

from bmd_sg.utilities import warn_moved

warn_moved(__name__)

__all__ = [
    "TiffMetadata",
    "load_chart_tiff",
]
