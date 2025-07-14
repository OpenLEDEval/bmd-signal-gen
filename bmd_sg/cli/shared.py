"""
Shared utilities for BMD CLI.

This module provides common device setup, configuration management,
and pattern generation utilities used across all CLI commands.
"""

import time

import numpy as np
import typer
from numpy.typing import ArrayLike

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    DecklinkSettings,
    HDRMetadata,
    PixelFormatType,
    get_decklink_devices,
    get_decklink_driver_version,
    get_decklink_sdk_version,
)
from bmd_sg.image_generators.checkerboard import ROI, PatternGenerator

# =============================================================================
# Device Discovery & Enumeration
# =============================================================================


def list_available_devices(show_logs: bool = True) -> list[str]:
    """
    List all available DeckLink devices.

    Parameters
    ----------
    show_logs : bool, optional
        Whether to print device information. Default is True.

    Returns
    -------
    list[str]
        List of available device names

    Raises
    ------
    RuntimeError
        If no DeckLink devices are found

    Examples
    --------
    >>> devices = list_available_devices()
    >>> print(f"Found {len(devices)} devices")
    """
    if show_logs:
        print(f"DeckLink driver/API version (runtime): {get_decklink_driver_version()}")
        print(f"DeckLink SDK version (build): {get_decklink_sdk_version()}")

    devices = get_decklink_devices()

    if show_logs:
        print("Available DeckLink devices:")
        for idx, name in enumerate(devices):
            print(f"  {idx}: {name}")

    if not devices:
        raise RuntimeError("No DeckLink devices found")

    return devices


def validate_device_index(device_index: int, devices: list[str]) -> None:
    """
    Validate that device index is within available range.

    Parameters
    ----------
    device_index : int
        Index of the DeckLink device to validate
    devices : list[str]
        List of available device names

    Raises
    ------
    RuntimeError
        If device index is out of range

    Examples
    --------
    >>> devices = list_available_devices()
    >>> validate_device_index(0, devices)
    """
    if device_index >= len(devices):
        raise RuntimeError(
            f"Device index {device_index} not found. Available devices: 0-{len(devices) - 1}"
        )


# =============================================================================
# Device Initialization & Configuration
# =============================================================================


def create_decklink_device(device_index: int) -> BMDDeckLink:
    """
    Create a DeckLink device instance.

    Parameters
    ----------
    device_index : int
        Index of the DeckLink device to create

    Returns
    -------
    BMDDeckLink
        Opened DeckLink device instance

    Raises
    ------
    RuntimeError
        If device creation fails

    Examples
    --------
    >>> device = create_decklink_device(0)
    """
    try:
        return BMDDeckLink(device_index=device_index)
    except Exception as e:
        raise RuntimeError(f"Failed to create DeckLink device: {e!s}")


def configure_pixel_format(
    decklink: BMDDeckLink,
    pixel_format: PixelFormatType | None = None,
    show_logs: bool = True,
) -> None:
    """
    Configure pixel format for the DeckLink device.

    Parameters
    ----------
    decklink : BMDDeckLink
        DeckLink device instance
    pixel_format : PixelFormatType | None, optional
        Specific pixel format to use. If None, auto-selects best format.
    show_logs : bool, optional
        Whether to print format selection information. Default is True.

    Raises
    ------
    RuntimeError
        If pixel format configuration fails

    Examples
    --------
    >>> configure_pixel_format(device)
    >>> configure_pixel_format(device, PixelFormatType.FORMAT_12BIT_RGBLE)
    """
    try:
        all_formats = decklink.get_supported_pixel_formats()

        # Filter out 8-bit and RGBX formats
        filtered_formats = []
        for pixel_fmt in all_formats:
            format_name = pixel_fmt.name
            if "8BIT" not in format_name and "RGBX" not in format_name:
                filtered_formats.append(pixel_fmt)

        if show_logs:
            print("\nPixel formats supported by device:")
            for idx, pixel_fmt in enumerate(filtered_formats):
                print(f"  {idx}: {pixel_fmt.name} ({pixel_fmt.bit_depth}-bit)")

        if pixel_format is None:
            # Auto-select best format
            preferred_formats = [
                PixelFormatType.FORMAT_12BIT_RGBLE,
                PixelFormatType.FORMAT_10BIT_RGB,
                PixelFormatType.FORMAT_10BIT_YUV,
                PixelFormatType.FORMAT_8BIT_BGRA,
                PixelFormatType.FORMAT_8BIT_ARGB,
            ]

            selected_pixel_format = None
            for preferred in preferred_formats:
                for pixel_fmt in filtered_formats:
                    if preferred == pixel_fmt:
                        selected_pixel_format = preferred
                        break
                if selected_pixel_format is not None:
                    break

            if selected_pixel_format is None:
                selected_pixel_format = filtered_formats[0]

            if show_logs:
                print(f"\nAuto-selected pixel format: {selected_pixel_format.name}")
        else:
            # Find the matching format in filtered_formats
            selected_pixel_format = None
            for pixel_fmt in filtered_formats:
                if pixel_format == pixel_fmt:
                    selected_pixel_format = pixel_format
                    break

            if selected_pixel_format is None:
                raise RuntimeError(
                    f"Pixel format {pixel_format.name} not found in supported formats"
                )

            if show_logs:
                print(f"\nUsing pixel format: {selected_pixel_format.name}")

        decklink.pixel_format = selected_pixel_format

    except Exception as e:
        raise RuntimeError(f"Failed to configure pixel format: {e!s}")


def configure_hdr_metadata(decklink: BMDDeckLink, settings: DecklinkSettings) -> None:
    """
    Configure HDR metadata for the DeckLink device.

    Parameters
    ----------
    decklink : BMDDeckLink
        DeckLink device instance
    settings : DecklinkSettings
        Settings containing HDR configuration

    Examples
    --------
    >>> configure_hdr_metadata(device, settings)
    """
    # Create HDR metadata
    hdr_metadata = HDRMetadata(
        eotf=settings.eotf,
        max_display_luminance=settings.max_display_mastering_luminance,
        min_display_luminance=settings.min_display_mastering_luminance,
        max_cll=settings.max_cll,
        max_fall=settings.max_fall,
    )

    # Set display primaries and white point chromaticity coordinates
    primary_coords = [
        ("Red", settings.red_primary),
        ("Green", settings.green_primary),
        ("Blue", settings.blue_primary),
        ("White", settings.white_point),
    ]

    for color, (x, y) in primary_coords:
        setattr(hdr_metadata.referencePrimaries, f"{color}X", float(x))
        setattr(hdr_metadata.referencePrimaries, f"{color}Y", float(y))

    # Set the complete HDR metadata (unless disabled)
    if not settings.no_hdr:
        decklink.set_hdr_metadata(hdr_metadata)
        print(
            f"Set complete HDR metadata: EOTF={settings.eotf}, MaxCLL={settings.max_cll}, MaxFALL={settings.max_fall}"
        )
    else:
        print(
            f"HDR metadata disabled. EOTF={settings.eotf}, MaxCLL={settings.max_cll}, MaxFALL={settings.max_fall}"
        )


def initialize_device(settings: DecklinkSettings) -> BMDDeckLink:
    """
    Complete device initialization with configuration.

    This function orchestrates the complete device setup workflow:
    1. List and validate available devices
    2. Create device instance
    3. Configure pixel format
    4. Configure HDR metadata
    5. Start playback

    Parameters
    ----------
    settings : DecklinkSettings
        Global device settings from CLI callback

    Returns
    -------
    BMDDeckLink
        Fully configured and started DeckLink device

    Raises
    ------
    RuntimeError
        If any step of device initialization fails

    Examples
    --------
    >>> device_settings = DeviceSettings(...)
    >>> device = initialize_device(device_settings)
    """
    try:
        # 1. Device discovery and validation
        devices = list_available_devices(show_logs=True)
        validate_device_index(settings.device, devices)

        # 2. Create device
        decklink = create_decklink_device(settings.device)

        # 3. Configure pixel format
        configure_pixel_format(decklink, settings.pixel_format, show_logs=True)

        # 4. Store frame dimensions
        decklink.width = settings.width
        decklink.height = settings.height

        # 5. Configure HDR metadata
        configure_hdr_metadata(decklink, settings)

        # 6. Start playback
        decklink.start_playback()

        return decklink

    except Exception as e:
        raise RuntimeError(f"Failed to initialize device: {e!s}") from e




# =============================================================================
# Pattern Generation Setup
# =============================================================================


def create_pattern_generator(
    decklink: BMDDeckLink, settings: DecklinkSettings
) -> PatternGenerator:
    """
    Create PatternGenerator with ROI from global settings.

    Uses the device's pixel format bit depth automatically.

    Parameters
    ----------
    decklink : BMDDeckLink
        Configured DeckLink device with pixel format set
    settings : DecklinkSettings
        Global device settings containing ROI configuration

    Returns
    -------
    PatternGenerator
        Configured pattern generator ready for use

    Examples
    --------
    >>> device = initialize_device(settings)
    >>> generator = create_pattern_generator(device, settings)
    """
    roi = ROI(
        x=settings.roi_x,
        y=settings.roi_y,
        width=settings.roi_width,
        height=settings.roi_height,
    )
    return PatternGenerator(
        bit_depth=decklink.pixel_format.bit_depth,
        width=settings.width,
        height=settings.height,
        roi=roi,
    )


def validate_color(value: ArrayLike, decklink: BMDDeckLink) -> np.ndarray:
    """
    Validate RGB color values against the device's bit depth.

    This function validates that RGB color values are within the valid range
    for the device's configured pixel format bit depth. Different bit depths
    have different maximum values: 8-bit (0-255), 10-bit (0-1023), 12-bit (0-4095).

    Parameters
    ----------
    value : ArrayLike
        RGB color values as array-like (list, tuple, or numpy array).
        Can be a single color [r, g, b] or multiple colors [[r1, g1, b1], [r2, g2, b2], ...]
    decklink : BMDDeckLink
        Configured DeckLink device with pixel format set

    Returns
    -------
    np.ndarray
        Validated RGB color array with same shape as input

    Raises
    ------
    typer.BadParameter
        If any color values are outside valid range for the bit depth

    Examples
    --------
    Validate single color against device bit depth:

    >>> device = initialize_device(settings)
    >>> validate_color([4095, 2048, 1024], device)
    array([4095, 2048, 1024])

    Validate multiple colors:

    >>> validate_color([[4095, 0, 0], [0, 4095, 0]], device)
    array([[4095,    0,    0],
           [   0, 4095,    0]])

    Invalid color values raise exception:

    >>> validate_color([4096, 0, 0], device)  # doctest: +SKIP
    typer.BadParameter: RGB values must be between 0 and 4095 for 12-bit

    Notes
    -----
    Bit depth determines the maximum color value:
    - 8-bit: 0-255 (2^8 - 1)
    - 10-bit: 0-1023 (2^10 - 1)
    - 12-bit: 0-4095 (2^12 - 1)
    - 16-bit: 0-65535 (2^16 - 1)

    This function automatically uses the device's configured pixel format
    bit depth for validation. The function uses numpy for efficient validation
    of color arrays.
    """
    bit_depth = decklink.pixel_format.bit_depth

    # Define max values for each supported bit depth
    max_value = 2**bit_depth - 1

    value = np.asarray(value)
    if not np.all((value >= 0) & (value <= max_value)):
        raise typer.BadParameter(
            f"RGB values must be between 0 and {max_value} for {bit_depth}-bit"
        )

    return value


# =============================================================================
# High-level Utilities
# =============================================================================


def get_device_settings(ctx: typer.Context) -> DecklinkSettings:
    """
    Extract DecklinkSettings from typer context.

    Parameters
    ----------
    ctx : typer.Context
        Typer context containing device settings

    Returns
    -------
    DecklinkSettings
        Global device settings from CLI callback

    Examples
    --------
    >>> settings = get_device_settings(ctx)
    >>> print(f"Device: {settings.device}")
    """
    return ctx.obj["device_settings"]


def display_image_for_duration(
    decklink: BMDDeckLink, image: np.ndarray, duration: float = 0
) -> None:
    """
    Display image and wait for specified duration.

    Parameters
    ----------
    decklink : BMDDeckLink
        Configured DeckLink device
    image : np.ndarray
        Image data to display (pattern, frame, or any image array)
    duration : float
        Duration in seconds to display the image

    Examples
    --------
    >>> display_image_for_duration(decklink, image, 5.0)
    Displaying image for 5.0 seconds...
    """
    decklink.display_frame(image)
    typer.echo(f"Displaying image for {duration} seconds...")
    time.sleep(duration)


def setup_tools_from_context(
    ctx: typer.Context,
) -> tuple[BMDDeckLink, PatternGenerator]:
    """
    Setup DeckLink device and pattern generator from typer context.

    This is the main entry point for all pattern commands. It handles
    the complete device initialization and pattern generator setup.

    Parameters
    ----------
    ctx : typer.Context
        Typer context containing device settings from CLI callback

    Returns
    -------
    tuple[BMDDeckLink, PatternGenerator]
        Initialized DeckLink device and pattern generator

    Raises
    ------
    RuntimeError
        If device setup fails at any stage

    Examples
    --------
    >>> @app.command()
    ... def pattern(ctx: typer.Context):
    ...     decklink, generator = setup_tools_from_context(ctx)
    ...     # Use decklink and generator...

    Notes
    -----
    This function extracts device settings from the typer context,
    initializes the DeckLink device with the specified configuration,
    and creates a pattern generator with the appropriate bit depth
    from the device's pixel format.
    """
    settings = get_device_settings(ctx)
    decklink = initialize_device(settings)
    generator = create_pattern_generator(decklink, settings)
    return decklink, generator
