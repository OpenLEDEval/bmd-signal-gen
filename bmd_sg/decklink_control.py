"""
This file holds the basic application structure for signal generation using a
DeckLink output device.
It can be executed directly from the command line as a script, or used as part
of the HTTP API.
"""

import time
from typing import Optional

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    EOTFType,
    PixelFormatType,
    get_decklink_devices,
    create_default_hdr_metadata,
    HDRMetadata,
)

from .patterns import PatternGenerator, PatternType

# Global DeckLink instance for API usage
decklink_instance = None
decklink_bit_depth = None


def determine_bit_depth(format_name: str) -> int:
    if "8" in format_name:
        return 8
    elif "10" in format_name:
        return 10
    else:
        return 12


def _initialize_decklink_device(
    device_index: int = 0,
    pixel_format_index: Optional[int] = None,
    show_logs: bool = True,
    use_global: bool = False,
):
    """Common DeckLink initialization logic. Returns (success, decklink, bit_depth, devices, error_msg)."""
    global decklink_instance, decklink_bit_depth

    try:
        from bmd_sg.decklink.bmd_decklink import (
            get_decklink_driver_version,
            get_decklink_sdk_version,
        )

        if show_logs:
            print(
                f"DeckLink driver/API version (runtime): {get_decklink_driver_version()}"
            )
            print(f"DeckLink SDK version (build): {get_decklink_sdk_version()}")

        devices = get_decklink_devices()
        if show_logs:
            print("Available DeckLink devices:")
            for idx, name in enumerate(devices):
                print(f"  {idx}: {name}")

        if not devices:
            return False, None, None, None, "No DeckLink devices found"

        if device_index >= len(devices):
            return (
                False,
                None,
                None,
                None,
                f"Device index {device_index} not found. Available devices: 0-{len(devices) - 1}",
            )

        decklink = BMDDeckLink(device_index=device_index)
        all_formats = decklink.get_supported_pixel_formats()
        filtered_formats = []
        format_mapping = []

        for idx, fmt in enumerate(all_formats):
            if "8" not in fmt and "RGBX" not in fmt:
                filtered_formats.append(fmt)
                format_mapping.append(idx)

        if show_logs:
            print(
                f"\nPixel formats supported by device {device_index} ({devices[device_index]}):"
            )
            for idx, fmt in enumerate(filtered_formats):
                print(f"  {idx}: {fmt}")

        if pixel_format_index is None:
            preferred_formats = [
                PixelFormatType.FORMAT_12BIT_RGBLE,
                PixelFormatType.FORMAT_10BIT_RGB,
                PixelFormatType.FORMAT_10BIT_YUV,
                PixelFormatType.FORMAT_8BIT_BGRA,
                PixelFormatType.FORMAT_8BIT_ARGB,
            ]
            selected_format = None

            for preferred in preferred_formats:
                for idx, fmt in enumerate(filtered_formats):
                    if preferred.value in fmt:
                        selected_format = idx
                        break
                if selected_format is not None:
                    break

            if selected_format is None:
                selected_format = 0

            if show_logs:
                print(
                    f"\nAuto-selected pixel format: {filtered_formats[selected_format]} (index {selected_format})"
                )

            original_index = format_mapping[selected_format]
        else:
            if pixel_format_index >= len(filtered_formats):
                return (
                    False,
                    None,
                    None,
                    None,
                    f"Pixel format index {pixel_format_index} not found",
                )

            original_index = format_mapping[pixel_format_index]
            selected_format = pixel_format_index

            if show_logs:
                print(
                    f"\nUsing pixel format: {filtered_formats[pixel_format_index]} (index {pixel_format_index})"
                )

        decklink.set_pixel_format(original_index)
        selected_format_name = filtered_formats[selected_format]
        bit_depth = determine_bit_depth(selected_format_name)

        if use_global:
            print(
                f"DEBUG: Setting global variables - decklink_instance={decklink}, bit_depth={bit_depth}"
            )
            decklink_instance = decklink
            decklink_bit_depth = bit_depth
            print(
                f"DEBUG: Global variables set - decklink_instance={decklink_instance}, decklink_bit_depth={decklink_bit_depth}"
            )

        return True, decklink, bit_depth, devices, None

    except Exception as e:
        return False, None, None, None, f"Failed to initialize DeckLink: {str(e)}"


def initialize_decklink_for_api(
    device_index: int = 0, pixel_format_index: Optional[int] = None
):
    """Initialize DeckLink for API usage. Returns (success, error_message)."""
    success, decklink, bit_depth, devices, error = _initialize_decklink_device(
        device_index, pixel_format_index, show_logs=True, use_global=True
    )
    return success, error


def create_api_args(
    width: int,
    height: int,
    pattern: PatternType,
    colors: list,
    roi_x: int = 0,
    roi_y: int = 0,
    roi_width: Optional[int] = None,
    roi_height: Optional[int] = None,
    duration: float = 5.0,
    no_hdr: bool = False,
    eotf: EOTFType = EOTFType.PQ,
    max_cll: int = 1000,
    max_fall: int = 400,
):
    class ApiArgs:
        def __init__(self):
            self.width = width
            self.height = height
            self.pattern = pattern
            self.roi_x = roi_x
            self.roi_y = roi_y
            self.roi_width = roi_width
            self.roi_height = roi_height
            self.duration = duration
            self.no_hdr = no_hdr
            self.eotf = eotf
            self.max_cll = max_cll
            self.max_fall = max_fall
            if len(colors) >= 1:
                self.r, self.g, self.b = colors[0]
            else:
                self.r, self.g, self.b = 4095, 0, 0
            if len(colors) >= 2:
                self.r2, self.g2, self.b2 = colors[1]
            else:
                self.r2, self.g2, self.b2 = 0, 0, 0
            if len(colors) >= 3:
                self.r3, self.g3, self.b3 = colors[2]
            else:
                self.r3, self.g3, self.b3 = 0, 0, 0
            if len(colors) >= 4:
                self.r4, self.g4, self.b4 = colors[3]
            else:
                self.r4, self.g4, self.b4 = 0, 0, 0

    return ApiArgs()


def generate_and_display_image(args, decklink, bit_depth):
    """Generate and display image with complete HDR metadata support."""
    try:
        # Start the DeckLink output first
        decklink.start()
        
        # Create pattern generator
        generator = PatternGenerator(
            width=args.width,
            height=args.height,
            bit_depth=bit_depth,
            pattern_type=args.pattern,
            roi_x=args.roi_x,
            roi_y=args.roi_y,
            roi_width=args.roi_width,
            roi_height=args.roi_height,
        )

        # Generate pattern based on type
        if args.pattern == PatternType.SOLID:
            image = generator.generate((args.r, args.g, args.b))
        elif args.pattern == PatternType.TWO_COLOR:
            image = generator.generate((args.r, args.g, args.b), (args.r2, args.g2, args.b2))
        elif args.pattern == PatternType.FOUR_COLOR:
            image = generator.generate(
                (args.r, args.g, args.b),
                (args.r2, args.g2, args.b2),
                (args.r3, args.g3, args.b3),
                (args.r4, args.g4, args.b4),
            )
        else:
            raise ValueError(f"Unsupported pattern type: {args.pattern}")

        # Set complete HDR metadata if not disabled
        if not args.no_hdr:
            # Create complete HDR metadata with default Rec2020 values
            hdr_metadata = create_default_hdr_metadata()

            # Update with user-provided values
            hdr_metadata.EOTF = args.eotf.value
            hdr_metadata.maxCLL = float(args.max_cll)
            hdr_metadata.maxFALL = float(args.max_fall)

            # Set the complete HDR metadata
            decklink.set_hdr_metadata(hdr_metadata)
            print(f"Set complete HDR metadata: EOTF={args.eotf}, MaxCLL={args.max_cll}, MaxFALL={args.max_fall}")
        else:
            # Use legacy EOTF method for SDR
            decklink.set_frame_eotf(args.eotf.value, args.max_cll, args.max_fall)
            print(f"Set basic EOTF metadata: EOTF={args.eotf}, MaxCLL={args.max_cll}, MaxFALL={args.max_fall}")

        # Set frame data and create frame
        decklink.set_frame_data(image)
        decklink.create_frame()
        decklink.schedule_frame()
        decklink.start_playback()

        print(f"Generated {args.pattern.value} pattern: {args.width}x{args.height}")
        
        return True

    except Exception as e:
        print(f"Error generating and displaying image: {e}")
        return False


def cleanup_decklink_device(decklink):
    print("Stopping output and closing device.")
    decklink.close()


def setup_decklink_device(args):
    """Setup DeckLink for CLI usage. Returns (decklink, bit_depth, devices)."""
    success, decklink, bit_depth, devices, error = _initialize_decklink_device(
        args.device, args.pixel_format, show_logs=True, use_global=False
    )
    if not success:
        print(f"Error: {error}")
        return None, None, None
    return decklink, bit_depth, devices
