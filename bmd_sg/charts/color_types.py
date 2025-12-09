"""
Color types and data structures for chart generation.

This module defines the core data types for representing color values,
patches, and chart layouts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Self

import numpy as np
from numpy.typing import NDArray


class ColorSpace(Enum):
    """Supported color spaces for chart generation."""

    XYZ = "XYZ"
    REC709 = "ITU-R BT.709"
    P3_D65 = "P3-D65"
    REC2020 = "ITU-R BT.2020"

    @classmethod
    def parse(cls, value: str) -> "ColorSpace":
        """
        Parse a colorspace from its string value.

        Parameters
        ----------
        value : str
            The colorspace string (e.g., "ITU-R BT.709", "ITU-R BT.2020").

        Returns
        -------
        ColorSpace
            The matching ColorSpace enum member.

        Raises
        ------
        ValueError
            If the value doesn't match any known colorspace.
        """
        for member in cls:
            if member.value == value:
                return member
        valid = ", ".join(f"'{m.value}'" for m in cls)
        raise ValueError(f"Unknown colorspace: '{value}'. Valid: {valid}")


class TransferFunction(Enum):
    """Supported transfer functions for encoding."""

    LINEAR = "linear"
    SRGB = "sRGB"
    GAMMA_22 = "gamma2.2"
    PQ = "ST.2084"
    HLG = "HLG"

    @classmethod
    def parse(cls, value: str) -> "TransferFunction":
        """
        Parse a transfer function from its string value.

        Parameters
        ----------
        value : str
            The transfer function string (e.g., "sRGB", "ST.2084").

        Returns
        -------
        TransferFunction
            The matching TransferFunction enum member.

        Raises
        ------
        ValueError
            If the value doesn't match any known transfer function.
        """
        for member in cls:
            if member.value == value:
                return member
        valid = ", ".join(f"'{m.value}'" for m in cls)
        raise ValueError(f"Unknown transfer function: '{value}'. Valid: {valid}")


@dataclass
class ColorValue:
    """
    A color value with its color space.

    Parameters
    ----------
    values : NDArray[np.float64]
        Color channel values (3 components).
    space : ColorSpace
        The color space of the values.
    """

    values: NDArray[np.float64]
    space: ColorSpace

    @classmethod
    def from_xyz(cls, x: float, y: float, z: float) -> Self:
        """Create a color value from XYZ tristimulus values."""
        return cls(values=np.array([x, y, z], dtype=np.float64), space=ColorSpace.XYZ)

    @classmethod
    def from_rgb(
        cls, r: float, g: float, b: float, space: ColorSpace = ColorSpace.REC709
    ) -> Self:
        """Create a color value from RGB values (0-1 normalized)."""
        return cls(values=np.array([r, g, b], dtype=np.float64), space=space)


@dataclass
class Patch:
    """
    A color patch with percentage-based position.

    Parameters
    ----------
    name : str
        Patch identifier (e.g., "GS 1", "Red").
    x_pct : float
        Left edge position as percentage (0.0-1.0).
    y_pct : float
        Top edge position as percentage (0.0-1.0).
    width_pct : float
        Width as percentage of total width (0.0-1.0).
    height_pct : float
        Height as percentage of total height (0.0-1.0).
    color : ColorValue
        The color of this patch.
    label_text : str | None
        Optional text to display on the patch for measurement validation.
    """

    name: str
    x_pct: float
    y_pct: float
    width_pct: float
    height_pct: float
    color: ColorValue
    label_text: str | None = None


@dataclass
class ChartLayout:
    """
    A complete chart layout with patches.

    Parameters
    ----------
    name : str
        Chart name (e.g., "My Color Chart").
    patches : list[Patch]
        List of color patches in the chart.
    source : str | None
        Source file or description.
    """

    name: str
    patches: list[Patch] = field(default_factory=list)
    source: str | None = None

    def add_patch(self, patch: Patch) -> None:
        """Add a patch to the layout."""
        self.patches.append(patch)
