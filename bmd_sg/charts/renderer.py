"""
Deprecated shim for ``display_patterns.charts.renderer``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.renderer`` imports keep working
for one release cycle. Import from ``display_patterns.charts.renderer``
instead.
"""

import warnings

from display_patterns.charts.renderer import render_chart

warnings.warn(
    "bmd_sg.charts.renderer is deprecated; "
    "import display_patterns.charts.renderer instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "render_chart",
]
