from typing import Tuple, List, Optional
from enum import Enum
import numpy as np

class PatternType(Enum):
    """Enumeration of supported pattern types."""
    SOLID = "solid"
    TWO_COLOR = "2color"
    FOUR_COLOR = "4color"

class ColorValidator:
    """Validates color values against bit depth ranges."""
    def __init__(self, bit_depth: int) -> None:
        self.bit_depth = bit_depth
        if bit_depth == 8:
            self.min_val, self.max_val = 0, 255
        elif bit_depth == 10:
            self.min_val, self.max_val = 0, 1023
        else:  # 12-bit
            self.min_val, self.max_val = 0, 4095

    def validate_color(self, r: int, g: int, b: int, color_name: str = "Color") -> None:
        """Validate RGB color values."""
        for component, name in [(r, f"{color_name} Red"), (g, f"{color_name} Green"), (b, f"{color_name} Blue")]:
            if not (self.min_val <= component <= self.max_val):
                raise ValueError(f"{name} value {component} is out of range for {self.bit_depth}-bit format ({self.min_val}-{self.max_val})")

    def validate_color_tuple(self, color_tuple: Tuple[int, int, int], color_name: str = "Color") -> None:
        """Validate RGB color tuple."""
        self.validate_color(*color_tuple, color_name)

class PatternGenerator:
    """Generates image patterns with validation and ROI support."""
    def __init__(self, width: int, height: int, bit_depth: int = 12, pattern_type: PatternType = PatternType.SOLID) -> None:
        self.width = width
        self.height = height
        self.bit_depth = bit_depth
        self.pattern_type = pattern_type
        self.validator = ColorValidator(bit_depth)

    def _create_image(self) -> np.ndarray:
        """Create a blank image with uint16 dtype."""
        return np.zeros((self.height, self.width, 3), dtype=np.uint16)

    def _validate_roi(self, roi_x: int, roi_y: int, roi_width: Optional[int], roi_height: Optional[int]) -> Tuple[int, int]:
        """Validate region of interest boundaries."""
        if roi_width is None:
            roi_width = self.width
        if roi_height is None:
            roi_height = self.height
        if roi_x < 0 or roi_y < 0 or roi_x + roi_width > self.width or roi_y + roi_height > self.height:
            raise ValueError(f"Region of interest ({roi_x},{roi_y},{roi_width},{roi_height}) is outside image boundaries ({self.width}x{self.height})")
        return roi_width, roi_height

    def _draw_checkerboard_pattern(self, image: np.ndarray, colors: List[Tuple[int, int, int]], 
                                 roi_x: int, roi_y: int, roi_width: Optional[int], roi_height: Optional[int]) -> None:
        """Draw checkerboard pattern within ROI."""
        roi_width, roi_height = self._validate_roi(roi_x, roi_y, roi_width, roi_height)
        for y in range(roi_y, roi_y + roi_height):
            for x in range(roi_x, roi_x + roi_width):
                pattern_x = x % 2
                pattern_y = y % 2
                color_index = pattern_y * 2 + pattern_x
                r, g, b = colors[color_index]
                image[y, x, 0] = r
                image[y, x, 1] = g
                image[y, x, 2] = b

    def generate_solid(self, r: int, g: int, b: int, roi_x: int = 0, roi_y: int = 0, 
                      roi_width: Optional[int] = None, roi_height: Optional[int] = None) -> np.ndarray:
        """Generate solid color pattern."""
        self.validator.validate_color(r, g, b, "Solid")
        image = self._create_image()
        colors = [(r, g, b), (r, g, b), (r, g, b), (r, g, b)]
        self._draw_checkerboard_pattern(image, colors, roi_x, roi_y, roi_width, roi_height)
        return image

    def generate_2color(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], 
                       roi_x: int = 0, roi_y: int = 0, roi_width: Optional[int] = None, roi_height: Optional[int] = None) -> np.ndarray:
        """Generate 2-color checkerboard pattern."""
        self.validator.validate_color_tuple(color1, "Color1")
        self.validator.validate_color_tuple(color2, "Color2")
        image = self._create_image()
        colors = [color1, color2, color2, color1]
        self._draw_checkerboard_pattern(image, colors, roi_x, roi_y, roi_width, roi_height)
        return image

    def generate_4color(self, colors: List[Tuple[int, int, int]], roi_x: int = 0, roi_y: int = 0, 
                       roi_width: Optional[int] = None, roi_height: Optional[int] = None) -> np.ndarray:
        """Generate 4-color checkerboard pattern."""
        if len(colors) != 4:
            raise ValueError("Must provide exactly 4 colors for 4-color checkerboard")
        for i, color in enumerate(colors, 1):
            self.validator.validate_color_tuple(color, f"Color{i}")
        image = self._create_image()
        self._draw_checkerboard_pattern(image, colors, roi_x, roi_y, roi_width, roi_height)
        return image

    def generate(self, color1: Tuple[int, int, int], color2: Optional[Tuple[int, int, int]] = None,
                color3: Optional[Tuple[int, int, int]] = None, color4: Optional[Tuple[int, int, int]] = None,
                roi_x: int = 0, roi_y: int = 0, roi_width: Optional[int] = None, roi_height: Optional[int] = None) -> np.ndarray:
        """Generate pattern based on pattern_type with the provided colors and print pattern info."""
        if self.pattern_type == PatternType.SOLID:
            r, g, b = color1
            print(f"\nGenerating solid color RGB({r}, {g}, {b}) for {self.bit_depth}-bit format...")
            return self.generate_solid(r, g, b, roi_x, roi_y, roi_width, roi_height)
        elif self.pattern_type == PatternType.TWO_COLOR:
            if color2 is None:
                color2 = (0, 0, 0)
            print(f"\nGenerating 2-color checkerboard RGB{color1} and RGB{color2} for {self.bit_depth}-bit format...")
            return self.generate_2color(color1, color2, roi_x, roi_y, roi_width, roi_height)
        elif self.pattern_type == PatternType.FOUR_COLOR:
            if color2 is None:
                color2 = (0, 0, 0)
            if color3 is None:
                color3 = (0, 0, 0)
            if color4 is None:
                color4 = (0, 0, 0)
            colors = [color1, color2, color3, color4]
            print(f"\nGenerating 4-color checkerboard for {self.bit_depth}-bit format...")
            print(f"  Colors: RGB{color1}, RGB{color2}, RGB{color3}, RGB{color4}")
            return self.generate_4color(colors, roi_x, roi_y, roi_width, roi_height)
        else:
            raise ValueError(f"Unsupported pattern type: {self.pattern_type}") 