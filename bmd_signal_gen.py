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

def generate_solid_color(width, height, r, g, b, bit_depth=12):
    """Generate solid color image as numpy array.
    
    Args:
        width, height: image dimensions
        r, g, b: color values (0-255 for 8-bit, 0-1023 for 10-bit, 0-4095 for 12-bit)
        bit_depth: bit depth (8, 10, or 12) - defaults to 12 for high quality
    
    Returns:
        numpy array with shape (height, width, 3) in uint16 format
    """
    # Always use uint16 for consistency
    image = np.zeros((height, width, 3), dtype=np.uint16)
    image[:, :, 0] = r
    image[:, :, 1] = g
    image[:, :, 2] = b
    return image

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
    parser.add_argument('--pattern', type=str, choices=['solid'], 
                       default='solid', help='Pattern type to generate (only "solid" is supported)')
    parser.add_argument('--width', type=int, default=1920, help='Image width (default: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='Image height (default: 1080)')
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
        if '8' not in fmt and 'RGBX' not in fmt and 'LE' not in fmt:
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

    for color_name, color_val in zip(['Red', 'Green', 'Blue'], [args.r, args.g, args.b]):
        if not (min_val <= color_val <= max_val):
            print(f"Error: {color_name} value {color_val} is out of range for {bit_depth}-bit format ({min_val}-{max_val})")
            return 1

    print(f"\nSetting color to RGB({args.r}, {args.g}, {args.b}) for {bit_depth}-bit format (range {min_val}-{max_val})...")
    
    # Only support solid color for now
    image = generate_solid_color(args.width, args.height, args.r, args.g, args.b, bit_depth)
    
    # Set the frame data using the new method with pixel format
    decklink.set_frame_data(image, original_index)
    
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
    decklink.start()
    print(f"Outputting for {args.duration} seconds...")
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    print("Stopping output and closing device.")
    decklink.close()

if __name__ == "__main__":
    main() 