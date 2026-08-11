"""
Deprecated shim for ``display_patterns.charts.tiff_reader``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.tiff_reader`` imports keep
working for one release cycle. Import from
``display_patterns.charts.tiff_reader`` instead.
"""

import warnings

from display_patterns.charts.tiff_reader import TiffMetadata, load_chart_tiff

warnings.warn(
    "bmd_sg.charts.tiff_reader is deprecated; "
    "import display_patterns.charts.tiff_reader instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "TiffMetadata",
    "load_chart_tiff",
]
