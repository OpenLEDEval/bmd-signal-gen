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
    def __init__(self, width: int, height: int, bit_depth: int = 12, pattern_type: PatternType = PatternType.SOLID,
                 roi_x: int = 0, roi_y: int = 0, roi_width: Optional[int] = None, roi_height: Optional[int] = None) -> None:
        self.width = width
        self.height = height
        self.bit_depth = bit_depth
        self.pattern_type = pattern_type
        self.validator = ColorValidator(bit_depth)
        self.roi_x = roi_x
        self.roi_y = roi_y
        self.roi_width = roi_width
        self.roi_height = roi_height

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

    def _validate_colors(self, colors: List[Tuple[int, int, int]]):
        for i, color in enumerate(colors, 1):
            self.validator.validate_color_tuple(color, f"Color{i}")

    def _print_pattern_info(self, pattern_type: PatternType, colors: List[Tuple[int, int, int]]):
        print(f"\nGenerating {pattern_type.value} pattern for {self.bit_depth}-bit format...")
        for i, color in enumerate(colors, 1):
            print(f"  Color {i}: RGB{color}")

    def _pad_colors(self, colors: List[Tuple[int, int, int]], required: int) -> List[Tuple[int, int, int]]:
        return colors + [(0, 0, 0)] * (required - len(colors))

    def _generate_solid(self, r: int, g: int, b: int) -> np.ndarray:
        colors = [(r, g, b)] * 4
        self._validate_colors(colors[:1])
        self._print_pattern_info(PatternType.SOLID, colors[:1])
        image = self._create_image()
        self._draw_checkerboard_pattern(image, colors, self.roi_x, self.roi_y, self.roi_width, self.roi_height)
        return image

    def _generate_2color(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> np.ndarray:
        colors = [color1, color2, color2, color1]
        self._validate_colors([color1, color2])
        self._print_pattern_info(PatternType.TWO_COLOR, [color1, color2])
        image = self._create_image()
        self._draw_checkerboard_pattern(image, colors, self.roi_x, self.roi_y, self.roi_width, self.roi_height)
        return image

    def _generate_4color(self, colors: List[Tuple[int, int, int]]) -> np.ndarray:
        if len(colors) != 4:
            raise ValueError("Must provide exactly 4 colors for 4-color checkerboard")
        self._validate_colors(colors)
        self._print_pattern_info(PatternType.FOUR_COLOR, colors)
        image = self._create_image()
        self._draw_checkerboard_pattern(image, colors, self.roi_x, self.roi_y, self.roi_width, self.roi_height)
        return image

    def generate(self, color1: Tuple[int, int, int], color2: Optional[Tuple[int, int, int]] = None,
                color3: Optional[Tuple[int, int, int]] = None, color4: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
        if self.pattern_type == PatternType.SOLID:
            return self._generate_solid(*color1)
        elif self.pattern_type == PatternType.TWO_COLOR:
            colors = self._pad_colors([color1, color2 or (0, 0, 0)], 2)
            return self._generate_2color(*colors)
        elif self.pattern_type == PatternType.FOUR_COLOR:
            colors = self._pad_colors([color1, color2 or (0, 0, 0), color3 or (0, 0, 0), color4 or (0, 0, 0)], 4)
            return self._generate_4color(colors)
        else:
            raise ValueError(f"Unsupported pattern type: {self.pattern_type}") 