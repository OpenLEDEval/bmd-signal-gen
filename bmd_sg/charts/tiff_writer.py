"""
Deprecated shim for ``display_patterns.charts.tiff_writer``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.tiff_writer`` imports keep
working for one release cycle. Import from
``display_patterns.charts.tiff_writer`` instead.
"""

import warnings

from display_patterns.charts.tiff_writer import ChartMetadata, write_chart_tiff

warnings.warn(
    "bmd_sg.charts.tiff_writer is deprecated; "
    "import display_patterns.charts.tiff_writer instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "ChartMetadata",
    "write_chart_tiff",
]
