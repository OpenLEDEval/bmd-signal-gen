"""
Chart generation module for BMD signal generator.

This module provides tools for creating display-ready test charts from
colorimetric data (XYZ, RGB, or built-in definitions like SMPTE bars).
Charts can include optional text labels for measurement validation
with spectroradiometers and colorimeters.
"""

from bmd_sg.charts.color_types import ChartLayout, ColorValue, Patch
from bmd_sg.charts.conversion import xyz_to_display_rgb
from bmd_sg.charts.renderer import render_chart
from bmd_sg.charts.tiff_reader import TiffMetadata, load_chart_tiff
from bmd_sg.charts.tiff_writer import write_chart_tiff

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
