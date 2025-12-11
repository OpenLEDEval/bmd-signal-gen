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


class Illuminant(Enum):
    """CIE standard illuminants for XYZ reference white."""

    D65 = "D65"  # Average daylight (~6500K), standard for broadcast/display
    D50 = "D50"  # Horizon light (~5000K), standard for print/ICC profiles
    D55 = "D55"  # Mid-morning/afternoon daylight (~5500K)
    A = "A"  # Incandescent/tungsten (~2856K)
    E = "E"  # Equal energy (theoretical reference)

    @classmethod
    def parse(cls, value: str) -> "Illuminant":
        """
        Parse an illuminant from its string value.

        Parameters
        ----------
        value : str
            The illuminant string (e.g., "D65", "D50").

        Returns
        -------
        Illuminant
            The matching Illuminant enum member.

        Raises
        ------
        ValueError
            If the value doesn't match any known illuminant.
        """
        for member in cls:
            if member.value == value:
                return member
        valid = ", ".join(f"'{m.value}'" for m in cls)
        raise ValueError(f"Unknown illuminant: '{value}'. Valid: {valid}")


class PatternType(Enum):
    """Pattern types for patch rendering.

    Defines how a patch should be rendered - either as a solid color
    or as a checkerboard pattern for gamma-invariant luminance measurement.

    Checkerboard patterns use 2×2 pixel repeating patterns of 100% white
    and 0% black to produce gamma-invariant luminance values:
    - CHECKERBOARD_25: 1 white + 3 black pixels = 25% luminance
    - CHECKERBOARD_50: 2 white + 2 black pixels = 50% luminance
    - CHECKERBOARD_75: 3 white + 1 black pixels = 75% luminance
    """

    SOLID = "solid"
    CHECKERBOARD_25 = "checkerboard_25"  # 2×2: 1 white, 3 black
    CHECKERBOARD_50 = "checkerboard_50"  # 2×2: 2 white, 2 black (diagonal)
    CHECKERBOARD_75 = "checkerboard_75"  # 2×2: 3 white, 1 black

    @classmethod
    def parse(cls, value: str) -> "PatternType":
        """
        Parse a pattern type from its string value.

        Parameters
        ----------
        value : str
            The pattern type string (e.g., "solid", "checkerboard_50").

        Returns
        -------
        PatternType
            The matching PatternType enum member.

        Raises
        ------
        ValueError
            If the value doesn't match any known pattern type.
        """
        for member in cls:
            if member.value == value:
                return member
        valid = ", ".join(f"'{m.value}'" for m in cls)
        raise ValueError(f"Unknown pattern type: '{value}'. Valid: {valid}")


@dataclass
class Colorimetry:
    """
    Colorimetry metadata for a chart.

    This captures the color space, illuminant, and normalization parameters
    needed to correctly interpret and convert the chart's color values.

    Parameters
    ----------
    color_space : ColorSpace
        The color space of the chart's color values.
    illuminant : Illuminant
        The CIE standard illuminant the XYZ values are referenced to.
    white_point : tuple[float, float]
        The white point chromaticity coordinates (x, y).
    reference_white_Y : float
        The Y value that corresponds to white (typically 100.0).
    """

    color_space: ColorSpace = ColorSpace.XYZ
    illuminant: Illuminant = Illuminant.D65
    white_point: tuple[float, float] = (0.3127, 0.329)  # D65 chromaticity
    reference_white_Y: float = 100.0


@dataclass
class AnnotationStripe:
    """
    Position of an annotation stripe.

    Parameters
    ----------
    y_start : float
        Starting Y position as percentage (0.0-1.0).
    y_end : float
        Ending Y position as percentage (0.0-1.0).
    """

    y_start: float
    y_end: float


@dataclass
class AnnotationLayout:
    """
    Layout positions for annotation stripes.

    Parameters
    ----------
    top_stripe : AnnotationStripe | None
        Top annotation stripe (typically for encoding info).
    bottom_stripe : AnnotationStripe | None
        Bottom annotation stripe (typically for chart metadata).
    """

    top_stripe: AnnotationStripe | None = None
    bottom_stripe: AnnotationStripe | None = None


@dataclass
class Canvas:
    """
    Chart canvas dimensions and embedding settings.

    The canvas defines the native size of the chart content. When rendering
    to a larger output frame, the chart is centered with surround color fill.

    Parameters
    ----------
    width : int
        Canvas width in pixels.
    height : int
        Canvas height in pixels.
    surround : tuple[float, float, float]
        RGB surround color (0.0-1.0) for embedding in larger frames.
        Default is black (0.0, 0.0, 0.0).
    """

    width: int = 1920
    height: int = 1080
    surround: tuple[float, float, float] = (0.0, 0.0, 0.0)


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
        The color of this patch (used for solid patterns, ignored for checkerboards).
    pattern : PatternType
        How to render the patch (solid color or checkerboard pattern).
    label_text : str | None
        Optional text to display on the patch for measurement validation.
    """

    name: str
    x_pct: float
    y_pct: float
    width_pct: float
    height_pct: float
    color: ColorValue
    pattern: PatternType = PatternType.SOLID
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
    colorimetry : Colorimetry | None
        Colorimetry metadata for the chart (illuminant, white point, etc.).
    annotations : AnnotationLayout | None
        Layout positions for annotation stripes.
    canvas : Canvas | None
        Canvas dimensions for chart rendering. If None, defaults to 1920x1080.
    """

    name: str
    patches: list[Patch] = field(default_factory=list)
    source: str | None = None
    colorimetry: Colorimetry | None = None
    annotations: AnnotationLayout | None = None
    canvas: Canvas | None = None

    def add_patch(self, patch: Patch) -> None:
        """Add a patch to the layout."""
        self.patches.append(patch)

