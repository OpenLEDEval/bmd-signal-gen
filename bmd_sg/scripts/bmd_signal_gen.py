#!/usr/bin/env python3
"""
Application to output a solid RGB color to a DeckLink device using the DeckLinkSignalGen wrapper.
Supports HDR metadata configuration including EOTF settings and pixel format selection.
"""

import argparse
import sys
import time

from fastapi import FastAPI

import bmd_sg.decklink_control as decklink_control
from bmd_sg.api import router as bmd_router
from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.decklink_control import (
    cleanup_decklink_device,
    decklink_instance,
    display_pattern,
    initialize_decklink_for_api,
    setup_decklink_device,
)
from bmd_sg.pattern_generator import (
    BIT_DEPTH_8_MAX,
    BIT_DEPTH_10_MAX,
    BIT_DEPTH_12_MAX,
    DEFAULT_BIT_DEPTH,
    DEFAULT_COLOR_12BIT,
    PatternType,
)
from bmd_sg.signal_generator import (
    D65_WHITE_POINT,
    DEFAULT_HEIGHT,
    DEFAULT_MAX_CLL,
    DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE,
    DEFAULT_MAX_FALL,
    DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE,
    DEFAULT_WIDTH,
    REC2020_BLUE_PRIMARY,
    REC2020_GREEN_PRIMARY,
    REC2020_RED_PRIMARY,
    DeckLinkSettings,
    PatternSettings,
)

pat_server = FastAPI()
pat_server.include_router(bmd_router)

# Global DeckLink instance for API usage
decklink_instance = None
decklink_bit_depth = None


class ChromaticityAction(argparse.Action):
    """Custom action for chromaticity coordinate pairs (x, y)."""

    def __call__(self, parser, namespace, values, option_string=None):
        if values is None or len(values) != 2:
            parser.error(f"{option_string} requires exactly 2 values (x y)")

        try:
            x, y = float(values[0]), float(values[1])
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                parser.error(f"{option_string} coordinates must be between 0.0 and 1.0")
        except ValueError:
            parser.error(f"{option_string} coordinates must be valid numbers")

        setattr(namespace, self.dest, (x, y))


@pat_server.on_event("startup")
async def startup_event():
    """Initialize DeckLink when FastAPI starts."""
    print("DEBUG: FastAPI startup event called")
    success, error = initialize_decklink_for_api()
    print(
        f"DEBUG: initialize_decklink_for_api returned: success={success}, error={error}"
    )
    if not success:
        print(f"Warning: Failed to initialize DeckLink for API: {error}")
    else:
        print("DeckLink initialized for API usage")


@pat_server.on_event("shutdown")
async def shutdown_event():
    """Clean up DeckLink when FastAPI shuts down."""
    if decklink_control.decklink_instance:
        cleanup_decklink_device(decklink_control.decklink_instance)


def main() -> int:
    description = (
        "Programatically output signals from a Blackmagic Design DeckLink "
        "device with HDR metadata support. The pattern can be configured by "
        "an http API for remote automation"
        "\n\nColor value ranges by pixel format:"
        f"\n  12-bit:  0-{BIT_DEPTH_12_MAX} (default, recommended)"
        f"\n  10-bit:  0-{BIT_DEPTH_10_MAX}"
        f"\n  8-bit:   0-{BIT_DEPTH_8_MAX} (fallback mode)"
        "\n\nPattern types:"
        "\n  solid: Single color (default)"
        "\n  2color: Two-color checkerboard"
        "\n  4color: Four-color checkerboard"
        "\n\nRegion of Interest:"
        "\n  Use --roi-x, --roi-y, --roi-width, --roi-height to limit pattern to a region"
    )
    parser = argparse.ArgumentParser(description=description)

    # Add arguments to the parser, directly mapping to SignalSettings fields
    parser.add_argument(
        "--device", "-d", type=int, default=0, help="Device index (default: 0)"
    )
    parser.add_argument(
        "--pixel-format",
        "-p",
        type=int,
        help="Pixel format index (leave blank for auto-select)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Image width (default: {DEFAULT_WIDTH})",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Image height (default: {DEFAULT_HEIGHT})",
    )
    parser.add_argument(
        "--pattern",
        type=PatternType,
        choices=list(PatternType),
        default=PatternType.SOLID,
        help="Pattern type to generate (default: solid)",
    )
    parser.add_argument(
        "--colors",
        nargs="+",
        type=int,
        default=list(DEFAULT_COLOR_12BIT),
        help=f"List of colors as R G B values. E.g., --colors {DEFAULT_COLOR_12BIT[0]} {DEFAULT_COLOR_12BIT[1]} {DEFAULT_COLOR_12BIT[2]} 0 {BIT_DEPTH_12_MAX} 0",
    )
    parser.add_argument(
        "--roi-x", type=int, default=0, help="Region of interest X offset (default: 0)"
    )
    parser.add_argument(
        "--roi-y", type=int, default=0, help="Region of interest Y offset (default: 0)"
    )
    parser.add_argument(
        "--roi-width",
        type=int,
        help="Region of interest width (default: full image width)",
    )
    parser.add_argument(
        "--roi-height",
        type=int,
        help="Region of interest height (default: full image height)",
    )
    parser.add_argument(
        "--no-hdr", action="store_true", help="Disable HDR metadata (use SDR mode)"
    )
    parser.add_argument(
        "--eotf",
        type=EOTFType.parse,
        choices=list(EOTFType),
        default=EOTFType.PQ,
        help="EOTF type (CEA 861.3): 1=SDR, 2=PQ, 3=HLG, (default: 2=PQ)",
    )
    parser.add_argument(
        "--max-cll",
        type=float,
        default=DEFAULT_MAX_CLL,
        help=f"Maximum Content Light Level in cd/m² (default: {DEFAULT_MAX_CLL})",
    )
    parser.add_argument(
        "--max-fall",
        type=float,
        default=DEFAULT_MAX_FALL,
        help=f"Maximum Frame Average Light Level in cd/m² (default: {DEFAULT_MAX_FALL})",
    )
    parser.add_argument(
        "--max-display-mastering-luminance",
        type=float,
        default=DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE,
        help=f"Maximum display mastering luminance in cd/m² (default: {DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE})",
    )
    parser.add_argument(
        "--min-display-mastering-luminance",
        type=float,
        default=DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE,
        help=f"Minimum display mastering luminance in cd/m² (default: {DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE})",
    )
    parser.add_argument(
        "--red-primary",
        nargs=2,
        type=float,
        default=REC2020_RED_PRIMARY,
        action=ChromaticityAction,
        metavar=("X", "Y"),
        help=f"Red primary coordinates (default: {REC2020_RED_PRIMARY[0]} {REC2020_RED_PRIMARY[1]} for Rec2020)",
    )
    parser.add_argument(
        "--green-primary",
        nargs=2,
        type=float,
        default=REC2020_GREEN_PRIMARY,
        action=ChromaticityAction,
        metavar=("X", "Y"),
        help=f"Green primary coordinates (default: {REC2020_GREEN_PRIMARY[0]} {REC2020_GREEN_PRIMARY[1]} for Rec2020)",
    )
    parser.add_argument(
        "--blue-primary",
        nargs=2,
        type=float,
        default=REC2020_BLUE_PRIMARY,
        action=ChromaticityAction,
        metavar=("X", "Y"),
        help=f"Blue primary coordinates (default: {REC2020_BLUE_PRIMARY[0]} {REC2020_BLUE_PRIMARY[1]} for Rec2020)",
    )
    parser.add_argument(
        "--white-point",
        nargs=2,
        type=float,
        default=D65_WHITE_POINT,
        action=ChromaticityAction,
        metavar=("X", "Y"),
        help=f"White point coordinates (default: {D65_WHITE_POINT[0]} {D65_WHITE_POINT[1]} for D65)",
    )
    parser.add_argument(
        "--duration",
        "-t",
        type=float,
        default=5.0,
        help="Duration in seconds (default: 5.0)",
    )

    args = parser.parse_args()

    # Group colors into tuples
    if len(args.colors) % 3 != 0:
        parser.error("Colors must be provided in groups of three (R G B)")
    colors = [tuple(args.colors[i : i + 3]) for i in range(0, len(args.colors), 3)]

    # Create DeckLinkSettings object from parsed arguments
    decklink_settings = DeckLinkSettings(
        width=args.width,
        height=args.height,
        no_hdr=args.no_hdr,
        eotf=args.eotf,
        max_cll=args.max_cll,
        max_fall=args.max_fall,
        max_display_mastering_luminance=args.max_display_mastering_luminance,
        min_display_mastering_luminance=args.min_display_mastering_luminance,
        red_primary=args.red_primary,
        green_primary=args.green_primary,
        blue_primary=args.blue_primary,
        white_point=args.white_point,
    )

    decklink, bit_depth, devices = setup_decklink_device(
        decklink_settings, args.device, args.pixel_format
    )
    if decklink is None:
        return 1

    # Create PatternSettings object from parsed arguments
    pattern_settings = PatternSettings(
        pattern=args.pattern,
        colors=colors,
        roi_x=args.roi_x,
        roi_y=args.roi_y,
        roi_width=args.roi_width,
        roi_height=args.roi_height,
        bit_depth=bit_depth if bit_depth is not None else DEFAULT_BIT_DEPTH,
    )

    success = display_pattern(pattern_settings, decklink)
    if success:
        # Wait for the specified duration only in CLI mode
        print(f"Displaying for {args.duration} seconds...")
        time.sleep(args.duration)

    cleanup_decklink_device(decklink)
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    if "--api" in sys.argv:
        import uvicorn

        uvicorn.run("bmd_signal_gen:app", host="127.0.0.1", port=8000, reload=True)
    else:
        sys.exit(main())
