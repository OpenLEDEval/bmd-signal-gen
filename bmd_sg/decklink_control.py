"""
This file holds the basic application structure for signal generation using a
DeckLink output device.
It can be executed directly from the command line as a script, or used as part
of the HTTP API.
"""

from typing import Optional

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    PixelFormatType,
    get_decklink_devices,
)

from bmd_sg.pattern_generator import PatternGenerator
from bmd_sg.signal_generator import DeckLinkSettings, PatternSettings

# Global DeckLink instance for API usage
decklink_instance = None
decklink_bit_depth = None
decklink_width = None
decklink_height = None


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
    global decklink_instance, decklink_bit_depth, decklink_width, decklink_height

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





def display_pattern(settings: PatternSettings, decklink: BMDDeckLink):
    """Generate and display a pattern on the DeckLink device."""
    try:
        # Create pattern generator
        generator = PatternGenerator(
            width=settings.width,
            height=settings.height,
            bit_depth=settings.bit_depth,
            pattern_type=settings.pattern,
            roi_x=settings.roi_x,
            roi_y=settings.roi_y,
            roi_width=settings.roi_width,
            roi_height=settings.roi_height,
        )

        # Generate pattern based on type
        image = generator.generate(settings.colors)

        # Set frame data and create frame
        decklink.set_frame_data(image)
        decklink.create_frame()
        decklink.schedule_frame()
        decklink.start_playback()

        print(f"Generated {settings.pattern.value} pattern: {settings.width}x{settings.height}")

        return True

    except Exception as e:
        print(f"Error generating and displaying image: {e}")
        return False


def cleanup_decklink_device(decklink):
    print("Stopping output and closing device.")
    decklink.close()


def setup_decklink_device(settings: DeckLinkSettings, device_index: int, pixel_format_index: Optional[int]):
    """Setup DeckLink for CLI usage. Returns (decklink, bit_depth, devices)."""
    success, decklink, bit_depth, devices, error = _initialize_decklink_device(
        device_index, pixel_format_index, show_logs=True, use_global=False
    )
    if not success:
        print(f"Error: {error}")
        return None, None, None

    # Store width and height for later use
    decklink.width = settings.width
    decklink.height = settings.height

    # Set complete HDR metadata if not disabled
    if not settings.no_hdr:
        # Create complete HDR metadata with default Rec2020 values
        hdr_metadata = create_default_hdr_metadata()

        # Update with user-provided values
        hdr_metadata.EOTF = settings.eotf.value
        hdr_metadata.maxCLL = float(settings.max_cll)
        hdr_metadata.maxFALL = float(settings.max_fall)
        # Set mastering display luminance
        hdr_metadata.maxDisplayMasteringLuminance = float(
            settings.max_display_mastering_luminance
        )
        hdr_metadata.minDisplayMasteringLuminance = float(
            settings.min_display_mastering_luminance
        )
        # Set display primaries and white point chromaticity coordinates
        hdr_metadata.referencePrimaries.RedX = float(settings.red_primary[0])
        hdr_metadata.referencePrimaries.RedY = float(settings.red_primary[1])
        hdr_metadata.referencePrimaries.GreenX = float(settings.green_primary[0])
        hdr_metadata.referencePrimaries.GreenY = float(settings.green_primary[1])
        hdr_metadata.referencePrimaries.BlueX = float(settings.blue_primary[0])
        hdr_metadata.referencePrimaries.BlueY = float(settings.blue_primary[1])
        hdr_metadata.referencePrimaries.WhiteX = float(settings.white_point[0])
        hdr_metadata.referencePrimaries.WhiteY = float(settings.white_point[1])

        # Set the complete HDR metadata
        decklink.set_hdr_metadata(hdr_metadata)
    else:
        # Use legacy EOTF method for SDR
        decklink.set_frame_eotf(
            settings.eotf.value, settings.max_cll, settings.max_fall
        )
        print(
            f"Set basic EOTF metadata: EOTF={settings.eotf}, MaxCLL={settings.max_cll}, MaxFALL={settings.max_fall}"
        )

    decklink.start()
    return decklink, bit_depth, devices
