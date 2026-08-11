"""
Deprecated shim for ``display_patterns.charts.renderer``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.renderer`` imports keep working
for one release cycle. Import from ``display_patterns.charts.renderer``
instead.
"""

from display_patterns.charts.renderer import render_chart

from bmd_sg.utilities import warn_moved

warn_moved(__name__)

__all__ = [
    "render_chart",
]
