#!/usr/bin/env python3
"""
Typer-based CLI for BMD Signal Generator.
Supports HDR metadata configuration including EOTF settings and pixel format selection.
"""

import time
from typing import Annotated

import typer
from typer import Argument, Option

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    EOTFType,
    HDRMetadata,
    PixelFormatType,
    get_decklink_devices,
    get_decklink_driver_version,
    get_decklink_sdk_version,
)
from bmd_sg.pattern_generator import ROI, PatternGenerator
from bmd_sg.signal_generator import DeckLinkSettings

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="BMD Signal Generator - Output test patterns to Blackmagic Design DeckLink devices",
)


def validate_color(value: tuple[int, int, int]) -> tuple[int, int, int]:
    """Validate RGB color values."""
    r, g, b = value
    if not all(0 <= val <= 4095 for val in [r, g, b]):
        raise typer.BadParameter("RGB values must be between 0 and 4095 for 12-bit")
    return (r, g, b)


@app.command()
def solid(
    # Color
    color: Annotated[
        tuple[int, int, int],
        Argument(help="RGB color values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (4095, 4095, 4095),
    duration: Annotated[
        float,
        Option(
            "--duration",
            "-t",
            help="Duration in seconds",
            rich_help_panel="Basic Settings",
        ),
    ] = 5,
    # Device / Pixel Format
    device: Annotated[
        int,
        Option(
            "--device",
            "-d",
            help="Device index",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = 0,
    pixel_format: Annotated[
        PixelFormatType | None,
        Option(
            "--pixel-format",
            "-p",
            help="Pixel format index (auto-select if not specified)",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = None,
    width: Annotated[
        int,
        Option("--width", help="Image width", rich_help_panel="Device / Pixel Format"),
    ] = 1920,
    height: Annotated[
        int,
        Option(
            "--height", help="Image height", rich_help_panel="Device / Pixel Format"
        ),
    ] = 1080,
    # ROI
    roi_x: Annotated[
        int, Option("--roi-x", help="ROI X offset", rich_help_panel="ROI")
    ] = 0,
    roi_y: Annotated[
        int, Option("--roi-y", help="ROI Y offset", rich_help_panel="ROI")
    ] = 0,
    roi_width: Annotated[
        int, Option("--roi-width", help="ROI width", rich_help_panel="ROI")
    ] = 1920,
    roi_height: Annotated[
        int, Option("--roi-height", help="ROI height", rich_help_panel="ROI")
    ] = 1080,
    # HDR Metadata
    eotf: Annotated[
        EOTFType,
        Option("--eotf", help="EOTF type (CEA 861.3)", rich_help_panel="HDR Metadata"),
    ] = EOTFType.PQ,
    max_display_mastering_luminance: Annotated[
        float,
        Option(
            "--max-display-mastering-luminance",
            help="Max display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 1000.0,
    min_display_mastering_luminance: Annotated[
        float,
        Option(
            "--min-display-mastering-luminance",
            help="Min display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 0.0,
    max_cll: Annotated[
        float,
        Option(
            "--max-cll",
            help="Maximum Content Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 10000.0,
    max_fall: Annotated[
        float,
        Option(
            "--max-fall",
            help="Maximum Frame Average Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 80.0,
    red_primary: Annotated[
        tuple[float, float],
        Option(
            "--red-primary",
            help="Red primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.708, 0.292),
    green_primary: Annotated[
        tuple[float, float],
        Option(
            "--green-primary",
            help="Green primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.170, 0.797),
    blue_primary: Annotated[
        tuple[float, float],
        Option(
            "--blue-primary",
            help="Blue primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.131, 0.046),
    white_primary: Annotated[
        tuple[float, float],
        Option(
            "--white-primary",
            help="White point coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.3127, 0.3290),
    no_hdr: Annotated[
        bool,
        Option("--no-hdr", help="Disable HDR metadata", rich_help_panel="HDR Metadata"),
    ] = False,
) -> None:
    """
    Generate and display solid color pattern on BMD DeckLink devices.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Pattern type: Single solid color
    """

    # Validate color
    color = validate_color(color)

    # Create DeckLink settings
    decklink_settings = DeckLinkSettings(
        width=width,
        height=height,
        no_hdr=no_hdr,
        eotf=eotf,
        max_cll=max_cll,
        max_fall=max_fall,
        max_display_mastering_luminance=max_display_mastering_luminance,
        min_display_mastering_luminance=min_display_mastering_luminance,
        red_primary=red_primary,
        green_primary=green_primary,
        blue_primary=blue_primary,
        white_point=white_primary,
    )

    # Setup DeckLink device
    decklink, bit_depth, _ = setup_decklink_device(
        decklink_settings, device, pixel_format
    )

    # Create ROI for pattern generation
    roi = ROI(x=roi_x, y=roi_y, width=roi_width, height=roi_height)

    # Generate solid color pattern
    generator = PatternGenerator(
        bit_depth=bit_depth or 12,
        width=width,
        height=height,
        roi=roi,
    )

    img = generator.generate([color])

    # Display the pattern
    decklink.display_frame(img)

    typer.echo(f"Displaying for {duration} seconds...")
    time.sleep(duration)


@app.command()
def pat2(
    # Colors
    color1: Annotated[
        tuple[int, int, int],
        Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (4095, 4095, 4095),
    color2: Annotated[
        tuple[int, int, int],
        Option(
            "--color2",
            help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit",
            rich_help_panel="Colors",
        ),
    ] = (0, 0, 0),
    duration: Annotated[
        float,
        Option(
            "--duration",
            "-t",
            help="Duration in seconds",
            rich_help_panel="Basic Settings",
        ),
    ] = 5,
    # Device / Pixel Format
    device: Annotated[
        int,
        Option(
            "--device",
            "-d",
            help="Device index",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = 0,
    pixel_format: Annotated[
        PixelFormatType | None,
        Option(
            "--pixel-format",
            "-p",
            help="Pixel format index (auto-select if not specified)",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = None,
    width: Annotated[
        int,
        Option("--width", help="Image width", rich_help_panel="Device / Pixel Format"),
    ] = 1920,
    height: Annotated[
        int,
        Option(
            "--height", help="Image height", rich_help_panel="Device / Pixel Format"
        ),
    ] = 1080,
    # ROI
    roi_x: Annotated[
        int, Option("--roi-x", help="ROI X offset", rich_help_panel="ROI")
    ] = 0,
    roi_y: Annotated[
        int, Option("--roi-y", help="ROI Y offset", rich_help_panel="ROI")
    ] = 0,
    roi_width: Annotated[
        int, Option("--roi-width", help="ROI width", rich_help_panel="ROI")
    ] = 1920,
    roi_height: Annotated[
        int, Option("--roi-height", help="ROI height", rich_help_panel="ROI")
    ] = 1080,
    # HDR Metadata
    eotf: Annotated[
        EOTFType,
        Option("--eotf", help="EOTF type (CEA 861.3)", rich_help_panel="HDR Metadata"),
    ] = EOTFType.PQ,
    max_display_mastering_luminance: Annotated[
        float,
        Option(
            "--max-display-mastering-luminance",
            help="Max display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 1000.0,
    min_display_mastering_luminance: Annotated[
        float,
        Option(
            "--min-display-mastering-luminance",
            help="Min display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 0.0001,
    max_cll: Annotated[
        float,
        Option(
            "--max-cll",
            help="Maximum Content Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 10000.0,
    max_fall: Annotated[
        float,
        Option(
            "--max-fall",
            help="Maximum Frame Average Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 80.0,
    red_primary: Annotated[
        tuple[float, float],
        Option(
            "--red-primary",
            help="Red primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.708, 0.292),
    green_primary: Annotated[
        tuple[float, float],
        Option(
            "--green-primary",
            help="Green primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.170, 0.797),
    blue_primary: Annotated[
        tuple[float, float],
        Option(
            "--blue-primary",
            help="Blue primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.131, 0.046),
    white_primary: Annotated[
        tuple[float, float],
        Option(
            "--white-primary",
            help="White point coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.3127, 0.3290),
    no_hdr: Annotated[
        bool,
        Option("--no-hdr", help="Disable HDR metadata", rich_help_panel="HDR Metadata"),
    ] = False,
) -> None:
    """
    Generate and display test patterns on BMD DeckLink devices.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Pattern type: Two-color checkerboard
    """

    # Validate colors
    color1 = validate_color(color1)
    color2 = validate_color(color2)

    # Create DeckLink settings
    decklink_settings = DeckLinkSettings(
        width=width,
        height=height,
        no_hdr=no_hdr,
        eotf=eotf,
        max_cll=max_cll,
        max_fall=max_fall,
        max_display_mastering_luminance=max_display_mastering_luminance,
        min_display_mastering_luminance=min_display_mastering_luminance,
        red_primary=red_primary,
        green_primary=green_primary,
        blue_primary=blue_primary,
        white_point=white_primary,
    )

    # Setup DeckLink device
    decklink, bit_depth, _ = setup_decklink_device(
        decklink_settings, device, pixel_format
    )

    # Create ROI for pattern generation
    roi = ROI(x=roi_x, y=roi_y, width=roi_width, height=roi_height)

    # Generate two-color checkerboard pattern
    generator = PatternGenerator(
        bit_depth=bit_depth or 12,
        width=width,
        height=height,
        roi=roi,
    )

    img = generator.generate([color1, color2])

    # Display the pattern
    decklink.display_frame(img)

    typer.echo(f"Displaying for {duration} seconds...")
    time.sleep(duration)


@app.command()
def pat3(
    # Colors
    color1: Annotated[
        tuple[int, int, int],
        Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (4095, 4095, 4095),
    color2: Annotated[
        tuple[int, int, int],
        Option(
            "--color2",
            help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit",
            rich_help_panel="Colors",
        ),
    ] = (0, 0, 0),
    color3: Annotated[
        tuple[int, int, int],
        Option(
            "--color3",
            help="Third color RGB values (r,g,b) - each 0-4095 for 12-bit",
            rich_help_panel="Colors",
        ),
    ] = (2048, 2048, 2048),
    duration: Annotated[
        float,
        Option(
            "--duration",
            "-t",
            help="Duration in seconds",
            rich_help_panel="Basic Settings",
        ),
    ] = 5,
    # Device / Pixel Format
    device: Annotated[
        int,
        Option(
            "--device",
            "-d",
            help="Device index",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = 0,
    pixel_format: Annotated[
        PixelFormatType | None,
        Option(
            "--pixel-format",
            "-p",
            help="Pixel format index (auto-select if not specified)",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = None,
    width: Annotated[
        int,
        Option("--width", help="Image width", rich_help_panel="Device / Pixel Format"),
    ] = 1920,
    height: Annotated[
        int,
        Option(
            "--height", help="Image height", rich_help_panel="Device / Pixel Format"
        ),
    ] = 1080,
    # ROI
    roi_x: Annotated[
        int, Option("--roi-x", help="ROI X offset", rich_help_panel="ROI")
    ] = 0,
    roi_y: Annotated[
        int, Option("--roi-y", help="ROI Y offset", rich_help_panel="ROI")
    ] = 0,
    roi_width: Annotated[
        int, Option("--roi-width", help="ROI width", rich_help_panel="ROI")
    ] = 1920,
    roi_height: Annotated[
        int, Option("--roi-height", help="ROI height", rich_help_panel="ROI")
    ] = 1080,
    # HDR Metadata
    eotf: Annotated[
        EOTFType,
        Option("--eotf", help="EOTF type (CEA 861.3)", rich_help_panel="HDR Metadata"),
    ] = EOTFType.PQ,
    max_display_mastering_luminance: Annotated[
        float,
        Option(
            "--max-display-mastering-luminance",
            help="Max display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 1000.0,
    min_display_mastering_luminance: Annotated[
        float,
        Option(
            "--min-display-mastering-luminance",
            help="Min display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 0.0001,
    max_cll: Annotated[
        float,
        Option(
            "--max-cll",
            help="Maximum Content Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 10000.0,
    max_fall: Annotated[
        float,
        Option(
            "--max-fall",
            help="Maximum Frame Average Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 80.0,
    red_primary: Annotated[
        tuple[float, float],
        Option(
            "--red-primary",
            help="Red primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.708, 0.292),
    green_primary: Annotated[
        tuple[float, float],
        Option(
            "--green-primary",
            help="Green primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.170, 0.797),
    blue_primary: Annotated[
        tuple[float, float],
        Option(
            "--blue-primary",
            help="Blue primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.131, 0.046),
    white_primary: Annotated[
        tuple[float, float],
        Option(
            "--white-primary",
            help="White point coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.3127, 0.3290),
    no_hdr: Annotated[
        bool,
        Option("--no-hdr", help="Disable HDR metadata", rich_help_panel="HDR Metadata"),
    ] = False,
) -> None:
    """
    Generate and display three-color checkerboard pattern on BMD DeckLink devices.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Pattern type: Three-color checkerboard (color1, color2, color3, color1)
    """

    # Validate colors
    color1 = validate_color(color1)
    color2 = validate_color(color2)
    color3 = validate_color(color3)

    # Create DeckLink settings
    decklink_settings = DeckLinkSettings(
        width=width,
        height=height,
        no_hdr=no_hdr,
        eotf=eotf,
        max_cll=max_cll,
        max_fall=max_fall,
        max_display_mastering_luminance=max_display_mastering_luminance,
        min_display_mastering_luminance=min_display_mastering_luminance,
        red_primary=red_primary,
        green_primary=green_primary,
        blue_primary=blue_primary,
        white_point=white_primary,
    )

    # Setup DeckLink device
    decklink, bit_depth, _ = setup_decklink_device(
        decklink_settings, device, pixel_format
    )

    # Create ROI for pattern generation
    roi = ROI(x=roi_x, y=roi_y, width=roi_width, height=roi_height)

    # Generate three-color checkerboard pattern
    generator = PatternGenerator(
        bit_depth=bit_depth or 12,
        width=width,
        height=height,
        roi=roi,
    )

    img = generator.generate([color1, color2, color3])

    # Display the pattern
    decklink.display_frame(img)

    typer.echo(f"Displaying for {duration} seconds...")
    time.sleep(duration)


@app.command()
def pat4(
    # Colors
    color1: Annotated[
        tuple[int, int, int],
        Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (4095, 4095, 4095),
    color2: Annotated[
        tuple[int, int, int],
        Option(
            "--color2",
            help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit",
            rich_help_panel="Colors",
        ),
    ] = (0, 0, 0),
    color3: Annotated[
        tuple[int, int, int],
        Option(
            "--color3",
            help="Third color RGB values (r,g,b) - each 0-4095 for 12-bit",
            rich_help_panel="Colors",
        ),
    ] = (2048, 2048, 2048),
    color4: Annotated[
        tuple[int, int, int],
        Option(
            "--color4",
            help="Fourth color RGB values (r,g,b) - each 0-4095 for 12-bit",
            rich_help_panel="Colors",
        ),
    ] = (1024, 1024, 1024),
    duration: Annotated[
        float,
        Option(
            "--duration",
            "-t",
            help="Duration in seconds",
            rich_help_panel="Basic Settings",
        ),
    ] = 5,
    # Device / Pixel Format
    device: Annotated[
        int,
        Option(
            "--device",
            "-d",
            help="Device index",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = 0,
    pixel_format: Annotated[
        PixelFormatType | None,
        Option(
            "--pixel-format",
            "-p",
            help="Pixel format index (auto-select if not specified)",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = None,
    width: Annotated[
        int,
        Option("--width", help="Image width", rich_help_panel="Device / Pixel Format"),
    ] = 1920,
    height: Annotated[
        int,
        Option(
            "--height", help="Image height", rich_help_panel="Device / Pixel Format"
        ),
    ] = 1080,
    # ROI
    roi_x: Annotated[
        int, Option("--roi-x", help="ROI X offset", rich_help_panel="ROI")
    ] = 0,
    roi_y: Annotated[
        int, Option("--roi-y", help="ROI Y offset", rich_help_panel="ROI")
    ] = 0,
    roi_width: Annotated[
        int, Option("--roi-width", help="ROI width", rich_help_panel="ROI")
    ] = 1920,
    roi_height: Annotated[
        int, Option("--roi-height", help="ROI height", rich_help_panel="ROI")
    ] = 1080,
    # HDR Metadata
    eotf: Annotated[
        EOTFType,
        Option("--eotf", help="EOTF type (CEA 861.3)", rich_help_panel="HDR Metadata"),
    ] = EOTFType.PQ,
    max_display_mastering_luminance: Annotated[
        float,
        Option(
            "--max-display-mastering-luminance",
            help="Max display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 1000.0,
    min_display_mastering_luminance: Annotated[
        float,
        Option(
            "--min-display-mastering-luminance",
            help="Min display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 0.0001,
    max_cll: Annotated[
        float,
        Option(
            "--max-cll",
            help="Maximum Content Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 10000.0,
    max_fall: Annotated[
        float,
        Option(
            "--max-fall",
            help="Maximum Frame Average Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 80.0,
    red_primary: Annotated[
        tuple[float, float],
        Option(
            "--red-primary",
            help="Red primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.708, 0.292),
    green_primary: Annotated[
        tuple[float, float],
        Option(
            "--green-primary",
            help="Green primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.170, 0.797),
    blue_primary: Annotated[
        tuple[float, float],
        Option(
            "--blue-primary",
            help="Blue primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.131, 0.046),
    white_primary: Annotated[
        tuple[float, float],
        Option(
            "--white-primary",
            help="White point coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.3127, 0.3290),
    no_hdr: Annotated[
        bool,
        Option("--no-hdr", help="Disable HDR metadata", rich_help_panel="HDR Metadata"),
    ] = False,
) -> None:
    """
    Generate and display four-color checkerboard pattern on BMD DeckLink devices.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Pattern type: Four-color checkerboard (color1, color2, color3, color4)
    """

    # Validate colors
    color1 = validate_color(color1)
    color2 = validate_color(color2)
    color3 = validate_color(color3)
    color4 = validate_color(color4)

    # Create DeckLink settings
    decklink_settings = DeckLinkSettings(
        width=width,
        height=height,
        no_hdr=no_hdr,
        eotf=eotf,
        max_cll=max_cll,
        max_fall=max_fall,
        max_display_mastering_luminance=max_display_mastering_luminance,
        min_display_mastering_luminance=min_display_mastering_luminance,
        red_primary=red_primary,
        green_primary=green_primary,
        blue_primary=blue_primary,
        white_point=white_primary,
    )

    # Setup DeckLink device
    decklink, bit_depth, _ = setup_decklink_device(
        decklink_settings, device, pixel_format
    )

    # Create ROI for pattern generation
    roi = ROI(x=roi_x, y=roi_y, width=roi_width, height=roi_height)

    # Generate four-color checkerboard pattern
    generator = PatternGenerator(
        bit_depth=bit_depth or 12,
        width=width,
        height=height,
        roi=roi,
    )

    img = generator.generate([color1, color2, color3, color4])

    # Display the pattern
    decklink.display_frame(img)

    typer.echo(f"Displaying for {duration} seconds...")
    time.sleep(duration)


@app.command()
def device_details() -> None:
    """Show details for all connected DeckLink devices."""

    try:
        # Print SDK and driver version information first
        typer.echo("DeckLink System Information:")
        typer.echo(f"  SDK Version: {get_decklink_sdk_version()}")
        typer.echo(f"  Driver Version: {get_decklink_driver_version()}")
        typer.echo()

        # Get all available devices
        devices = get_decklink_devices()

        if not devices:
            typer.echo("No DeckLink devices found.")
            return

        typer.echo(f"Found {len(devices)} DeckLink device(s):\n")

        # Iterate through each device
        for idx, device_name in enumerate(devices):
            typer.echo(f"Device {idx}: {device_name}")

            try:
                # Open the device to get its details using context manager
                with BMDDeckLink(device_index=idx) as decklink:
                    # Get supported pixel formats
                    formats = decklink.get_supported_pixel_formats()
                    typer.echo(f"  Supported pixel formats ({len(formats)}):")
                    for format_idx, pixel_format in enumerate(formats):
                        typer.echo(f"    {format_idx}: {pixel_format.name} ({pixel_format.bit_depth}-bit)")

                    # Check HDR support
                    hdr_support = decklink.supports_hdr
                    typer.echo(f"  HDR Support: {'Yes' if hdr_support else 'No'}")
                    # Device automatically closed when exiting with block

            except RuntimeError as e:
                typer.echo(f"  Error accessing device: {e}")

            typer.echo()  # Empty line between devices

    except Exception as e:
        typer.echo(f"Error enumerating devices: {e}", err=True)
        raise typer.Exit(1)



def _initialize_decklink_device(
    device_index: int = 0,
    pixel_format_index: PixelFormatType | None = None,
    show_logs: bool = True,
) -> tuple[bool, BMDDeckLink | None, int | None, list[str] | None, str | None]:
    """Common DeckLink initialization logic with device enumeration and format selection.

    Handles the complete device initialization workflow including device enumeration,
    pixel format selection (with auto-selection if not specified), and device opening.
    Provides detailed logging output when enabled.

    Parameters
    ----------
    device_index : int, optional
        Index of the DeckLink device to initialize. Default is 0.
    pixel_format_index : PixelFormatType | None, optional
        PixelFormatType enum value specifying the pixel format to use. If None,
        auto-selects the best available format (preferring 12-bit RGB). Default is None.
    show_logs : bool, optional
        Whether to print initialization progress and device information.
        Default is True.

    Returns
    -------
    tuple[bool, BMDDeckLink | None, int | None, list[str] | None, str | None]
        A tuple containing:
        - success: True if initialization succeeded, False otherwise
        - decklink: The opened BMDDeckLink device instance, or None on failure
        - bit_depth: The bit depth of the selected pixel format, or None on failure
        - devices: List of all available device names, or None on failure
        - error_msg: Error message string if success is False, None on success

    Notes
    -----
    The function performs automatic pixel format filtering, removing 8-bit and
    RGBX formats from consideration during auto-selection. It prefers formats
    in this order: 12-bit RGB LE, 10-bit RGB, 10-bit YUV, 8-bit BGRA, 8-bit ARGB.

    Examples
    --------
    >>> success, device, depth, devices, error = _initialize_decklink_device()
    >>> if success:
    ...     print(f"Initialized device with {depth}-bit depth")
    ... else:
    ...     print(f"Failed: {error}")
    """
    try:
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

        for idx, pixel_format in enumerate(all_formats):
            # Filter out 8-bit and RGBX formats based on format name
            format_name = pixel_format.name
            if "8BIT" not in format_name and "RGBX" not in format_name:
                filtered_formats.append(pixel_format)
                format_mapping.append(idx)

        if show_logs:
            print(
                f"\nPixel formats supported by device {device_index} ({devices[device_index]}):"
            )
            for idx, pixel_format in enumerate(filtered_formats):
                print(f"  {idx}: {pixel_format.name} ({pixel_format.bit_depth}-bit)")

        if pixel_format_index is None:
            preferred_formats = [
                PixelFormatType.FORMAT_12BIT_RGBLE,
                PixelFormatType.FORMAT_10BIT_RGB,
                PixelFormatType.FORMAT_10BIT_YUV,
                PixelFormatType.FORMAT_8BIT_BGRA,
                PixelFormatType.FORMAT_8BIT_ARGB,
            ]
            selected_format = None
            selected_pixel_format = None

            for preferred in preferred_formats:
                for idx, pixel_format in enumerate(filtered_formats):
                    if preferred == pixel_format:
                        selected_format = idx
                        selected_pixel_format = preferred
                        break
                if selected_format is not None:
                    break

            if selected_format is None:
                selected_format = 0
                # Fall back to the first available format
                selected_pixel_format = filtered_formats[0]

            if show_logs:
                print(
                    f"\nAuto-selected pixel format: {selected_pixel_format.name} (index {selected_format})"
                )

            original_index = format_mapping[selected_format]
        else:
            # Find the matching format in filtered_formats using the enum value
            selected_format = None
            selected_pixel_format = pixel_format_index
            for idx, pixel_format in enumerate(filtered_formats):
                if pixel_format_index == pixel_format:
                    selected_format = idx
                    break

            if selected_format is None:
                return (
                    False,
                    None,
                    None,
                    None,
                    f"Pixel format {pixel_format_index.name} not found in supported formats",
                )

            original_index = format_mapping[selected_format]

            if show_logs:
                print(
                    f"\nUsing pixel format: {selected_pixel_format.name} (index {selected_format})"
                )

        decklink.pixel_format = original_index
        bit_depth = selected_pixel_format.bit_depth

        return True, decklink, bit_depth, devices, None

    except Exception as e:
        return False, None, None, None, f"Failed to initialize DeckLink: {e!s}"



def setup_decklink_device(
    settings: DeckLinkSettings, device_index: int, pixel_format_index: PixelFormatType | None
) -> tuple[BMDDeckLink, int, list[str]]:
    """Setup DeckLink for CLI usage. Returns (decklink, bit_depth, devices)."""
    success, decklink, bit_depth, devices, error = _initialize_decklink_device(
        device_index, pixel_format_index, show_logs=True
    )
    if not success:
        raise RuntimeError(f"Failed to setup DeckLink device: {error}")

    # Store width and height for later use
    decklink.width = settings.width
    decklink.height = settings.height

    # Create HDR metadata using constructor parameters
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

    decklink.start_playback()
    return decklink, bit_depth, devices


if __name__ == "__main__":
    app()
