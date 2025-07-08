#!/usr/bin/env python3
"""
Application to output a solid RGB color to a DeckLink device using the DeckLinkSignalGen wrapper.
Supports HDR metadata configuration including EOTF settings and pixel format selection.
"""
import sys
import time
import argparse
import numpy as np
from lib.bmd_decklink import BMDDeckLink, get_decklink_devices, get_decklink_driver_version, get_decklink_sdk_version

def generate_4color_checkerboard(width, height, colors, bit_depth=12, roi_x=0, roi_y=0, roi_width=None, roi_height=None):
    """Generate 4-color checkerboard pattern as numpy array with optional region-of-interest.
    
    Args:
        width, height: image dimensions
        colors: list of 4 RGB tuples [(r1,g1,b1), (r2,g2,b2), (r3,g3,b3), (r4,g4,b4)]
        bit_depth: bit depth (8, 10, or 12) - defaults to 12 for high quality
        roi_x, roi_y: region-of-interest offset (default: 0, 0)
        roi_width, roi_height: region-of-interest dimensions (default: full image)
    
    Returns:
        numpy array with shape (height, width, 3) in uint16 format
    """
    if len(colors) != 4:
        raise ValueError("Must provide exactly 4 colors for 4-color checkerboard")
    
    # Always use uint16 for consistency
    image = np.zeros((height, width, 3), dtype=np.uint16)
    
    # Set ROI dimensions if not specified
    if roi_width is None:
        roi_width = width
    if roi_height is None:
        roi_height = height
    
    # Validate ROI boundaries
    if roi_x < 0 or roi_y < 0 or roi_x + roi_width > width or roi_y + roi_height > height:
        raise ValueError(f"Region of interest ({roi_x},{roi_y},{roi_width},{roi_height}) is outside image boundaries ({width}x{height})")
    
    # Create checkerboard pattern only within ROI
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
    
    return image

def generate_2color_checkerboard(width, height, color1, color2, bit_depth=12, roi_x=0, roi_y=0, roi_width=None, roi_height=None):
    """Generate 2-color checkerboard pattern as numpy array with optional region-of-interest.
    
    Args:
        width, height: image dimensions
        color1, color2: RGB tuples (r,g,b) for the two colors
        bit_depth: bit depth (8, 10, or 12) - defaults to 12 for high quality
        roi_x, roi_y: region-of-interest offset (default: 0, 0)
        roi_width, roi_height: region-of-interest dimensions (default: full image)
    
    Returns:
        numpy array with shape (height, width, 3) in uint16 format
    """
    # Create 4-color checkerboard with two colors in checkerboard order
    colors = [color1, color2, color2, color1]
    return generate_4color_checkerboard(width, height, colors, bit_depth, roi_x, roi_y, roi_width, roi_height)

def generate_solid_color(width, height, r, g, b, bit_depth=12, roi_x=0, roi_y=0, roi_width=None, roi_height=None):
    """Generate solid color image as numpy array with optional region-of-interest.
    
    Args:
        width, height: image dimensions
        r, g, b: color values (0-255 for 8-bit, 0-1023 for 10-bit, 0-4095 for 12-bit)
        bit_depth: bit depth (8, 10, or 12) - defaults to 12 for high quality
        roi_x, roi_y: region-of-interest offset (default: 0, 0)
        roi_width, roi_height: region-of-interest dimensions (default: full image)
    
    Returns:
        numpy array with shape (height, width, 3) in uint16 format
    """
    # Create 4-color checkerboard with same color repeated
    colors = [(r, g, b), (r, g, b), (r, g, b), (r, g, b)]
    return generate_4color_checkerboard(width, height, colors, bit_depth, roi_x, roi_y, roi_width, roi_height)

def main():
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
    parser.add_argument('--pattern', type=str, choices=['solid', '2color', '4color'], 
                       default='solid', help='Pattern type to generate (default: solid)')
    parser.add_argument('--width', type=int, default=1920, help='Image width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Image height (default: 1080)')
    parser.add_argument('--all', type=bool, default=False, help='Show all supported pixel formats')
    
    # Region of Interest arguments
    parser.add_argument('--roi-x', type=int, default=0, help='Region of interest X offset (default: 0)')
    parser.add_argument('--roi-y', type=int, default=0, help='Region of interest Y offset (default: 0)')
    parser.add_argument('--roi-width', type=int, help='Region of interest width (default: full image width)')
    parser.add_argument('--roi-height', type=int, help='Region of interest height (default: full image height)')
    
    # Two-color checkerboard arguments
    parser.add_argument('--r2', type=int, help='Red component for color 2 (2color pattern)')
    parser.add_argument('--g2', type=int, help='Green component for color 2 (2color pattern)')
    parser.add_argument('--b2', type=int, help='Blue component for color 2 (2color pattern)')
    
    # Four-color checkerboard arguments
    parser.add_argument('--r3', type=int, help='Red component for color 3 (4color pattern)')
    parser.add_argument('--g3', type=int, help='Green component for color 3 (4color pattern)')
    parser.add_argument('--b3', type=int, help='Blue component for color 3 (4color pattern)')
    parser.add_argument('--r4', type=int, help='Red component for color 4 (4color pattern)')
    parser.add_argument('--g4', type=int, help='Green component for color 4 (4color pattern)')
    parser.add_argument('--b4', type=int, help='Blue component for color 4 (4color pattern)')
    
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
    
    # After pixel format selection, determine bit depth and validate color arguments
    bit_depth = 12  # Default to 12-bit for high quality
    min_val, max_val = 0, 4095  # default to 12-bit min and max
    selected_format_name = filtered_formats[selected_format] if args.pixel_format is None or args.pixel_format == -1 else filtered_formats[args.pixel_format]
    if '8' in selected_format_name:
        bit_depth = 8
        min_val, max_val = 0, 255
    elif '10' in selected_format_name:
        bit_depth = 10
        min_val, max_val = 0, 1023
    # 12-bit is already the default

    # Validate color arguments based on pattern type
    try:
        if args.pattern == 'solid':
            for color_name, color_val in zip(['Red', 'Green', 'Blue'], [args.r, args.g, args.b]):
                if not (min_val <= color_val <= max_val):
                    print(f"Error: {color_name} value {color_val} is out of range for {bit_depth}-bit format ({min_val}-{max_val})")
                    return 1
            
            print(f"\nGenerating solid color RGB({args.r}, {args.g}, {args.b}) for {bit_depth}-bit format (range {min_val}-{max_val})...")
            image = generate_solid_color(args.width, args.height, args.r, args.g, args.b, bit_depth, 
                                      args.roi_x, args.roi_y, args.roi_width, args.roi_height)
            
        elif args.pattern == '2color':
            if args.r2 is None or args.g2 is None or args.b2 is None:
                print("Error: --r2, --g2, and --b2 are required for 2color pattern")
                return 1
            
            # Validate all colors
            for color_name, color_val in zip(['Red', 'Green', 'Blue', 'Red2', 'Green2', 'Blue2'], 
                                           [args.r, args.g, args.b, args.r2, args.g2, args.b2]):
                if not (min_val <= color_val <= max_val):
                    print(f"Error: {color_name} value {color_val} is out of range for {bit_depth}-bit format ({min_val}-{max_val})")
                    return 1
            
            color1 = (args.r, args.g, args.b)
            color2 = (args.r2, args.g2, args.b2)
            print(f"\nGenerating 2-color checkerboard RGB({args.r},{args.g},{args.b}) and RGB({args.r2},{args.g2},{args.b2}) for {bit_depth}-bit format...")
            image = generate_2color_checkerboard(args.width, args.height, color1, color2, bit_depth,
                                               args.roi_x, args.roi_y, args.roi_width, args.roi_height)
            
        elif args.pattern == '4color':
            if any(arg is None for arg in [args.r2, args.g2, args.b2, args.r3, args.g3, args.b3, args.r4, args.g4, args.b4]):
                print("Error: --r2, --g2, --b2, --r3, --g3, --b3, --r4, --g4, and --b4 are required for 4color pattern")
                return 1
            
            # Validate all colors
            for color_name, color_val in zip(['Red', 'Green', 'Blue', 'Red2', 'Green2', 'Blue2', 'Red3', 'Green3', 'Blue3', 'Red4', 'Green4', 'Blue4'], 
                                           [args.r, args.g, args.b, args.r2, args.g2, args.b2, args.r3, args.g3, args.b3, args.r4, args.g4, args.b4]):
                if not (min_val <= color_val <= max_val):
                    print(f"Error: {color_name} value {color_val} is out of range for {bit_depth}-bit format ({min_val}-{max_val})")
                    return 1
            
            colors = [(args.r, args.g, args.b), (args.r2, args.g2, args.b2),
                     (args.r3, args.g3, args.b3), (args.r4, args.g4, args.b4)]
            print(f"\nGenerating 4-color checkerboard for {bit_depth}-bit format...")
            print(f"  Colors: RGB({args.r},{args.g},{args.b}), RGB({args.r2},{args.g2},{args.b2}), RGB({args.r3},{args.g3},{args.b3}), RGB({args.r4},{args.g4},{args.b4})")
            image = generate_4color_checkerboard(args.width, args.height, colors, bit_depth,
                                               args.roi_x, args.roi_y, args.roi_width, args.roi_height)
            
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

if __name__ == "__main__":
    main() 