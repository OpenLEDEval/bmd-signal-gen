"""
Deprecated shim for ``display_patterns.charts.loaders``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.loaders`` imports keep working
for one release cycle. Import from ``display_patterns.charts.loaders``
instead.
"""

from display_patterns.charts.loaders import load_chart

from bmd_sg.utilities import warn_moved

warn_moved(__name__)

__all__ = [
    "load_chart",
]
