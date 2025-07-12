"""Pattern generator for creating test patterns with validation and ROI support.

This module provides functionality to generate checkerboard test patterns with
validation for color values and support for regions of interest (ROI). The patterns
are generated as NumPy arrays suitable for video output.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass
class ROI:
    """Region of Interest for pattern generation.

    Defines a rectangular region within an image where patterns will be drawn.
    Width and height define the size of the rectangular region.

    Parameters
    ----------
    x : int, optional
        X coordinate of the top-left corner. Default is 0.
    y : int, optional
        Y coordinate of the top-left corner. Default is 0.
    width : int, optional
        Width of the ROI in pixels. Default is 100.
    height : int, optional
        Height of the ROI in pixels. Default is 100.

    Examples
    --------
    Create a full-image ROI:

    >>> roi = ROI()
    >>> print(f"Position: ({roi.x}, {roi.y})")
    Position: (0, 0)

    Create a centered ROI:

    >>> roi = ROI(x=100, y=100, width=800, height=600)
    >>> print(f"ROI: {roi.width}x{roi.height} at ({roi.x}, {roi.y})")
    ROI: 800x600 at (100, 100)
    """

    x: int = 0
    y: int = 0
    width: int = 100
    height: int = 100

    @property
    def x2(self):
        return self.x + self.width

    @property
    def y2(self):
        return self.y + self.height


class ColorRangeError(RuntimeError):
    """Exception raised when color values are outside the valid range.

    This exception is raised when color values exceed the maximum value
    for the specified bit depth (e.g., values > 255 for 8-bit, > 4095 for 12-bit).

    Parameters
    ----------
    detail_string : str, optional
        Additional detail about the validation error.

    Examples
    --------
    >>> raise ColorRangeError("Value 300 exceeds 8-bit maximum of 255")
    ColorRangeError: colors must be a required bit-depth range.
    """

    def __init__(self, detail_string: str | None = None):
        super().__init__("colors must be a required bit-depth range.")
        if detail_string:
            self.add_note(detail_string)


def _validate_color(color1: ArrayLike, bitdepth: int = 8) -> bool:
    """Validate RGB color values against bit depth constraints.

    Checks that all color values are within the valid range [0, 2^bitdepth - 1].
    For example, 8-bit colors must be in range [0, 255], 12-bit in range [0, 4095].

    Parameters
    ---------
    color1 : ArrayLike
        Color values to validate. Can be a single color (3,) or multiple colors (N, 3).
    bitdepth : int, optional
        Bit depth for validation. Default is 8.

    Returns
    -------
    bool
        True if all color values are within valid range, False otherwise.

    Examples
    --------
    Validate 8-bit RGB color:

    >>> _validate_color([255, 128, 0], bitdepth=8)
    True
    >>> _validate_color([256, 128, 0], bitdepth=8)  # Value too high
    False

    Validate 12-bit RGB colors:

    >>> colors = [[4095, 2048, 0], [1024, 512, 256]]
    >>> _validate_color(colors, bitdepth=12)
    True
    """
    color1 = np.asarray(color1)
    # Check if all values are in valid range [0, 2^bitdepth - 1]
    return np.all(np.logical_and(color1 >= 0, color1 <= (2**bitdepth - 1))).item()


class PatternGenerator:
    """Generates image patterns with validation and ROI support.

    This class creates test patterns (currently checkerboard) for video output.
    It supports region-of-interest (ROI) rendering and validates color values
    against the specified bit depth.

    Parameters
    ----------
    bit_depth : int
        Bit depth for color values (e.g., 8, 10, 12).
    width : int
        Image width in pixels.
    height : int
        Image height in pixels.
    roi : ROI, optional
        Region of interest for pattern generation. If None, uses full image.

    Attributes
    ----------
    width : int
        Image width in pixels.
    height : int
        Image height in pixels.
    bit_depth : int
        Bit depth for color validation.
    roi : ROI
        Region of interest for pattern generation.

    Examples
    --------
    Create a pattern generator for 1080p 12-bit output:

    >>> generator = PatternGenerator(bit_depth=12, width=1920, height=1080)
    >>> colors = [[4095, 0, 0], [0, 4095, 0], [0, 0, 4095], [4095, 4095, 4095]]
    >>> pattern = generator.generate(colors)
    >>> print(f"Pattern shape: {pattern.shape}")
    Pattern shape: (1080, 1920, 3)

    Create with custom ROI:

    >>> roi = ROI(x=100, y=100, width=800, height=600)
    >>> generator = PatternGenerator(bit_depth=8, width=1920, height=1080, roi=roi)
    """

    def __init__(
        self,
        *,
        bit_depth: int,
        width: int,
        height: int,
        roi: ROI | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.bit_depth = bit_depth

        if roi is None:
            self.roi = ROI(0, 0, self.width, self.height)
        else:
            self.roi = roi

    def _draw_checkerboard_pattern(self, colors: ArrayLike) -> np.ndarray:
        """Draw checkerboard pattern within the specified ROI.

        Creates a 2x2 checkerboard pattern using the provided colors.
        The pattern alternates between the four colors in a checkerboard layout:
        - Top-left: colors[0]
        - Top-right: colors[1]
        - Bottom-left: colors[2]
        - Bottom-right: colors[3]

        Parameters
        ----------
        colors : ArrayLike
            Array of 4 RGB colors with shape (4, 3).

        Returns
        -------
        np.ndarray
            Image array with checkerboard pattern drawn in ROI.

        Raises
        ------
        RuntimeError
            If colors array doesn't have shape (4, 3).
        ColorRangeError
            If color values are outside valid range for bit depth.
        """
        colors = np.asarray(colors).copy()
        if colors.shape != (4, 3):
            raise RuntimeError("colors must be a list of (4,3) colors")

        # Validate all color values are within bit depth range
        if not _validate_color(colors, self.bit_depth):
            raise ColorRangeError(f"Bit depth: {self.bit_depth:d}")

        colors = np.vstack((colors, (0, 0, 0)))
        color_mask = np.full((self.height, self.width), 4, dtype=np.int32)

        # This section uses advanced indexing to quickly create this array with
        # numpy Do not refactor into for loops.

        # Ensure ROI is within image bounds
        roi_y_end = min(self.roi.y2, self.height)
        roi_x_end = min(self.roi.x2, self.width)
        
        # Set color indices based on coordinate parity
        color_mask[
            np.arange(self.roi.y, roi_y_end, 2).reshape((-1, 1)),
            np.arange(self.roi.x, roi_x_end, 2).reshape((1, -1)),
        ] = 0  # Even row, even column -> color 0
        color_mask[
            np.arange(self.roi.y + 1, roi_y_end, 2).reshape((-1, 1)),
            np.arange(self.roi.x, roi_x_end, 2).reshape((1, -1)),
        ] = 1  # Odd row, even column -> color 1
        color_mask[
            np.arange(self.roi.y, roi_y_end, 2).reshape((-1, 1)),
            np.arange(self.roi.x + 1, roi_x_end, 2).reshape((1, -1)),
        ] = 2  # Even row, odd column -> color 2
        color_mask[
            np.arange(self.roi.y + 1, roi_y_end, 2).reshape((-1, 1)),
            np.arange(self.roi.x + 1, roi_x_end, 2).reshape((1, -1)),
        ] = 3  # Odd row, odd column -> color 3

        # End Numpy advanced indexing.

        # Apply colors using advanced indexing
        o_image = colors[color_mask].copy()
        return np.ascontiguousarray(o_image.astype(np.uint16))

    def generate(self, colors: ArrayLike) -> np.ndarray:
        """Generate a checkerboard pattern with the specified colors.

        Accepts 1-4 colors and automatically expands them to create a 4-color
        checkerboard pattern. Color expansion rules:
        - 1 color: All four squares use the same color
        - 2 colors: Alternating pattern (color1, color2, color1, color2)
        - 3 colors: Custom mapping (color1, color2, color3, color2)
        - 4 colors: Direct mapping to checker squares

        Parameters
        ----------
        colors : ArrayLike
            Color array. Accepted shapes:
            - (3,) for single RGB color
            - (1, 3) for single RGB color
            - (2, 3) for two RGB colors
            - (3, 3) for three RGB colors
            - (4, 3) for four RGB colors

        Returns
        -------
        np.ndarray
            Generated pattern image with shape (height, width, 3).

        Raises
        ------
        RuntimeError
            If colors array has invalid shape.
        ColorRangeError
            If color values exceed bit depth limits.

        Examples
        --------
        Generate pattern with single color:

        >>> generator = PatternGenerator(bit_depth=8, width=100, height=100)
        >>> pattern = generator.generate([255, 0, 0])  # Red

        Generate pattern with four different colors:

        >>> colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]]
        >>> pattern = generator.generate(colors)
        """
        colors = np.asarray(colors)

        # Handle single color input: reshape (3,) to (1, 3)
        if colors.shape == (3,):
            colors = colors.reshape((1, 3))

        # Validate input shape: must be 2D with 1-4 rows and exactly 3 columns
        if (
            colors.ndim != 2
            or colors.shape[0] < 1
            or colors.shape[0] > 4
            or colors.shape[1] != 3
        ):
            raise RuntimeError(
                "Colors must have shape (1,3) to (4,3), or single color shape (3,)"
            )

        num_colors = colors.shape[0]

        # Expand colors to 4-color checkerboard pattern
        if num_colors == 1:
            # Single color: use same color for all four squares
            colors = np.broadcast_to(colors, (4, 3))
        elif num_colors == 2:
            # Two colors: tile to create checkerboard of two colors
            colors = colors[(0, 1, 1, 0), :]
        elif num_colors == 3:
            # Three colors: map to [color1, color2, color1, color3]
            # This creates a pattern where color1 appears in top-left and bottom-right
            colors = colors[(0, 1, 2, 0), :]

        return self._draw_checkerboard_pattern(colors)


# Default pattern generator for common 1080p 12-bit use case
# Uses 100-pixel border ROI to create centered pattern (1720x880 active area)
# Creates centered pattern within specified ROI
DEFAULT_PATTERN_GENERATOR = PatternGenerator(
    bit_depth=12,
    width=1920,
    height=1080,
    roi=ROI(x=100, y=100, width=1920 - 200, height=1080 - 200),
)

# Pre-generated pattern with 12-bit white/black checkerboard
# White: 2000/4095 ≈ 49% of 12-bit range (conservative for HDR displays)
# Black: 0/4095 = 0% (minimum luminance)
DEFAULT_PATTERN_BUFFER = DEFAULT_PATTERN_GENERATOR.generate(
    ((2000, 2000, 2000), (0, 0, 0))
)
