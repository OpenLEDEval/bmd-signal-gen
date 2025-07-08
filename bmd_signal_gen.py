#!/usr/bin/env python3
"""
Application to output a solid RGB color to a DeckLink device using the DeckLinkSignalGen wrapper.
Supports HDR metadata configuration including EOTF settings and pixel format selection.
"""
import sys
import time
import argparse
import numpy as np
from typing import Tuple, List, Optional, Union
from enum import Enum
from lib.bmd_decklink import BMDDeckLink, get_decklink_devices, get_decklink_driver_version, get_decklink_sdk_version

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
                # Determine which position in the 2x2 pattern this pixel belongs to
                pattern_x = x % 2
                pattern_y = y % 2
                
                # Map 2x2 position to color index
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
        colors = [color1, color2, color2, color1]  # Checkerboard order
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
                color2 = (0, 0, 0)  # Default to black
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

def determine_bit_depth(format_name: str) -> int:
    """Determine bit depth from pixel format name."""
    if '8' in format_name:
        return 8
    elif '10' in format_name:
        return 10
    else:  # 12-bit is default
        return 12

def main() -> int:
    print(f"DeckLink driver/API version (runtime): {get_decklink_driver_version()}")
    print(f"DeckLink SDK version (build): {get_decklink_sdk_version()}")
    devices = get_decklink_devices()
    print("Available DeckLink devices:")
    for idx, name in enumerate(devices):
        print(f"  {idx}: {name}")
    
    if not devices:
        print("No DeckLink devices found.")
        return 1
    
    description = (
        'Output solid RGB color to DeckLink device with HDR metadata support'
        '\n\nColor value ranges by pixel format:'
        '\n  12-bit:  0-4095 (default, recommended)'
        '\n  10-bit:  0-1023'
        '\n  8-bit:   0-255 (fallback mode)'
        '\n\nPattern types:'
        '\n  solid: Single color (default)'
        '\n  2color: Two-color checkerboard'
        '\n  4color: Four-color checkerboard'
        '\n\nRegion of Interest:'
        '\n  Use --roi-x, --roi-y, --roi-width, --roi-height to limit pattern to a region'
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('r', type=int, help='Red component (see --help for range)')
    parser.add_argument('g', type=int, help='Green component (see --help for range)')
    parser.add_argument('b', type=int, help='Blue component (see --help for range)')
    parser.add_argument('--duration', '-t', type=float, default=5.0, help='Duration in seconds (default: 5.0)')
    parser.add_argument('--device', '-d', type=int, default=0, help='Device index (default: 0)')
    parser.add_argument('--pixel-format', '-p', type=int, help='Pixel format index (use -1 for auto-select)')
    parser.add_argument('--eotf', type=int, choices=[0, 1, 2, 3, 4], default=3, 
                       help='EOTF type (CEA 861.3): 0=Reserved, 1=SDR, 2=HDR, 3=PQ, 4=HLG (default: 3=PQ)')
    parser.add_argument('--max-cll', type=int, default=1000, 
                       help='Maximum Content Light Level in cd/m² (default: 1000)')
    parser.add_argument('--max-fall', type=int, default=400, 
                       help='Maximum Frame Average Light Level in cd/m² (default: 400)')
    parser.add_argument('--no-hdr', action='store_true', 
                       help='Disable HDR metadata (use SDR mode)')
    parser.add_argument(
        '--pattern',
        type=PatternType,  # This will call PatternType('solid'), etc.
        choices=list(PatternType),
        default=PatternType.SOLID,
        help='Pattern type to generate (default: solid)'
    )
    parser.add_argument('--width', type=int, default=1920, help='Image width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Image height (default: 1080)')
    parser.add_argument('--all', type=bool, default=False, help='Show all supported pixel formats')
    
    # Region of Interest arguments
    parser.add_argument('--roi-x', type=int, default=0, help='Region of interest X offset (default: 0)')
    parser.add_argument('--roi-y', type=int, default=0, help='Region of interest Y offset (default: 0)')
    parser.add_argument('--roi-width', type=int, default=None, help='Region of interest width (default: full image width)')
    parser.add_argument('--roi-height', type=int, default=None, help='Region of interest height (default: full image height)')
    
    # Two-color checkerboard arguments
    parser.add_argument('--r2', type=int, default=0, help='Red component for color 2 (2color pattern, default: 0)')
    parser.add_argument('--g2', type=int, default=0, help='Green component for color 2 (2color pattern, default: 0)')
    parser.add_argument('--b2', type=int, default=0, help='Blue component for color 2 (2color pattern, default: 0)')
    
    # Four-color checkerboard arguments
    parser.add_argument('--r3', type=int, default=0, help='Red component for color 3 (4color pattern, default: 0)')
    parser.add_argument('--g3', type=int, default=0, help='Green component for color 3 (4color pattern, default: 0)')
    parser.add_argument('--b3', type=int, default=0, help='Blue component for color 3 (4color pattern, default: 0)')
    parser.add_argument('--r4', type=int, default=0, help='Red component for color 4 (4color pattern, default: 0)')
    parser.add_argument('--g4', type=int, default=0, help='Green component for color 4 (4color pattern, default: 0)')
    parser.add_argument('--b4', type=int, default=0, help='Blue component for color 4 (4color pattern, default: 0)')
    
    args = parser.parse_args()

    # Validate device index
    if args.device >= len(devices):
        print(f"Error: Device index {args.device} not found. Available devices: 0-{len(devices)-1}")
        return 1

    decklink = BMDDeckLink(device_index=args.device)
    
    # Get all supported pixel formats from C++
    all_formats = decklink.get_supported_pixel_formats()

    # Create a mapping of filtered formats to original indices
    filtered_formats = []
    format_mapping = []  # Maps filtered index to original index
    
    for idx, fmt in enumerate(all_formats):
        if args.all or ('8' not in fmt and 'RGBX' not in fmt and 'LE' not in fmt):
            filtered_formats.append(fmt)
            format_mapping.append(idx)
    
    print(f"\nPixel formats supported by device {args.device} ({devices[args.device]}):")
    for idx, fmt in enumerate(filtered_formats):
        print(f"  {idx}: {fmt}")
    
    # Auto-select pixel format if not specified
    if args.pixel_format is None or args.pixel_format == -1:
        # Try to find preferred formats in order: 12-bit formats first, then 10-bit, then 8-bit
        preferred_formats = ['12BitRGB', '10BitRGB', '10BitYUV', '8BitBGRA', '8BitARGB']
        selected_format = None
        
        for preferred in preferred_formats:
            for idx, fmt in enumerate(filtered_formats):
                if preferred in fmt:
                    selected_format = idx
                    break
            if selected_format is not None:
                break
        
        if selected_format is None:
            selected_format = 0  # Fallback to first available format
        
        print(f"\nAuto-selected pixel format: {filtered_formats[selected_format]} (index {selected_format})")
        # Map filtered index to original C++ index
        original_index = format_mapping[selected_format]
    else:
        # Use specified pixel format
        if args.pixel_format >= len(filtered_formats):
            print(f"Error: Pixel format index {args.pixel_format} not found. Available formats: 0-{len(filtered_formats)-1}")
            return 1
        print(f"\nUsing pixel format: {filtered_formats[args.pixel_format]} (index {args.pixel_format})")
        # Map filtered index to original C++ index
        original_index = format_mapping[args.pixel_format]
    
    decklink.set_pixel_format(original_index)
    
    # Determine bit depth from selected format
    selected_format_name = filtered_formats[selected_format] if args.pixel_format is None or args.pixel_format == -1 else filtered_formats[args.pixel_format]
    bit_depth = determine_bit_depth(selected_format_name)
    
    # Create pattern generator with validation
    pattern_gen = PatternGenerator(args.width, args.height, bit_depth, args.pattern)
    
    # Generate pattern based on type (printing is now handled inside generate)
    try:
        color1 = (args.r, args.g, args.b)
        color2 = (args.r2, args.g2, args.b2) if args.pattern in [PatternType.TWO_COLOR, PatternType.FOUR_COLOR] else None
        color3 = (args.r3, args.g3, args.b3) if args.pattern == PatternType.FOUR_COLOR else None
        color4 = (args.r4, args.g4, args.b4) if args.pattern == PatternType.FOUR_COLOR else None
        
        image = pattern_gen.generate(color1, color2, color3, color4, args.roi_x, args.roi_y, args.roi_width, args.roi_height)
            
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Log ROI information if specified
    if args.roi_x != 0 or args.roi_y != 0 or args.roi_width is not None or args.roi_height is not None:
        roi_w = args.roi_width if args.roi_width is not None else args.width
        roi_h = args.roi_height if args.roi_height is not None else args.height
        print(f"  Region of Interest: ({args.roi_x},{args.roi_y}) {roi_w}x{roi_h}")
    
    # Set the frame data using the new method with pixel format
    decklink.set_frame_data(image)
    
    # Configure HDR metadata (set once, before any color/output)
    if args.no_hdr:
        print(f"\nConfiguring device for SDR output (EOTF: SDR)")
        eotf_setting = 1  # CEA 861.3: 1 = Traditional gamma - SDR
        max_cll_setting = 0
        max_fall_setting = 0
    else:
        eotf_names = {0: "Reserved", 1: "SDR", 2: "HDR", 3: "PQ", 4: "HLG"}
        print(f"\nConfiguring device for HDR output:")
        print(f"  EOTF: {eotf_names[args.eotf]} ({args.eotf})")
        print(f"  Max CLL: {args.max_cll} cd/m²")
        print(f"  Max FALL: {args.max_fall} cd/m²")
        eotf_setting = args.eotf
        max_cll_setting = args.max_cll
        max_fall_setting = args.max_fall
    decklink.set_frame_eotf(eotf=eotf_setting, maxCLL=max_cll_setting, maxFALL=max_fall_setting)
    
    print("Starting output...")
    # Enable video output
    decklink.start()
    # Create frame from pending data
    decklink.create_frame()
    # Schedule the frame
    decklink.schedule_frame()
    # Start playback
    decklink.start_playback()
    print(f"Outputting for {args.duration} seconds...")
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    print("Stopping output and closing device.")
    decklink.close()

    return 0

if __name__ == "__main__":
    sys.exit(main()) 