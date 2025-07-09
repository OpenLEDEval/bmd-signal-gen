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
    generate_and_display_image,
    initialize_decklink_for_api,
    setup_decklink_device,
)
from bmd_sg.patterns import PatternType

pat_server = FastAPI()
pat_server.include_router(bmd_router)

# Global DeckLink instance for API usage
decklink_instance = None
decklink_bit_depth = None


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
        "Output solid RGB color to DeckLink device with HDR metadata support"
        "\n\nColor value ranges by pixel format:"
        "\n  12-bit:  0-4095 (default, recommended)"
        "\n  10-bit:  0-1023"
        "\n  8-bit:   0-255 (fallback mode)"
        "\n\nPattern types:"
        "\n  solid: Single color (default)"
        "\n  2color: Two-color checkerboard"
        "\n  4color: Four-color checkerboard"
        "\n\nRegion of Interest:"
        "\n  Use --roi-x, --roi-y, --roi-width, --roi-height to limit pattern to a region"
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "r", type=int, default=4095, help="Red component (see --help for range)"
    )
    parser.add_argument(
        "g", type=int, default=0, help="Green component (see --help for range)"
    )
    parser.add_argument(
        "b", type=int, default=0, help="Blue component (see --help for range)"
    )
    parser.add_argument(
        "--duration",
        "-t",
        type=float,
        default=5.0,
        help="Duration in seconds (default: 5.0)",
    )
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
        "--eotf",
        type=EOTFType.parse,
        choices=list(EOTFType),
        default=EOTFType.PQ,
        help="EOTF type (CEA 861.3): 1=SDR, 2=PQ, 3=HLG, (default: 2=PQ)",
    )
    parser.add_argument(
        "--max-cll",
        type=int,
        default=1000,
        help="Maximum Content Light Level in cd/m² (default: 1000)",
    )
    parser.add_argument(
        "--max-fall",
        type=int,
        default=400,
        help="Maximum Frame Average Light Level in cd/m² (default: 400)",
    )
    parser.add_argument(
        "--no-hdr", action="store_true", help="Disable HDR metadata (use SDR mode)"
    )
    parser.add_argument(
        "--pattern",
        type=PatternType,  # This will call PatternType('solid'), etc.
        choices=list(PatternType),
        default=PatternType.TWO_COLOR,
        help="Pattern type to generate (default: solid)",
    )
    parser.add_argument(
        "--width", type=int, default=1920, help="Image width (default: 1920)"
    )
    parser.add_argument(
        "--height", type=int, default=1080, help="Image height (default: 1080)"
    )
    parser.add_argument(
        "--all", type=bool, default=False, help="Show all supported pixel formats"
    )

    # Region of Interest arguments
    parser.add_argument(
        "--roi-x", type=int, default=64, help="Region of interest X offset (default: 0)"
    )
    parser.add_argument(
        "--roi-y", type=int, default=64, help="Region of interest Y offset (default: 0)"
    )
    parser.add_argument(
        "--roi-width",
        type=int,
        default=64,
        help="Region of interest width (default: full image width)",
    )
    parser.add_argument(
        "--roi-height",
        type=int,
        default=64,
        help="Region of interest height (default: full image height)",
    )

    # Two-color checkerboard arguments
    parser.add_argument(
        "--r2",
        type=int,
        default=0,
        help="Red component for color 2 (2color pattern, default: 0)",
    )
    parser.add_argument(
        "--g2",
        type=int,
        default=0,
        help="Green component for color 2 (2color pattern, default: 0)",
    )
    parser.add_argument(
        "--b2",
        type=int,
        default=0,
        help="Blue component for color 2 (2color pattern, default: 0)",
    )

    # Four-color checkerboard arguments
    parser.add_argument(
        "--r3",
        type=int,
        default=0,
        help="Red component for color 3 (4color pattern, default: 0)",
    )
    parser.add_argument(
        "--g3",
        type=int,
        default=0,
        help="Green component for color 3 (4color pattern, default: 0)",
    )
    parser.add_argument(
        "--b3",
        type=int,
        default=0,
        help="Blue component for color 3 (4color pattern, default: 0)",
    )
    parser.add_argument(
        "--r4",
        type=int,
        default=0,
        help="Red component for color 4 (4color pattern, default: 0)",
    )
    parser.add_argument(
        "--g4",
        type=int,
        default=0,
        help="Green component for color 4 (4color pattern, default: 0)",
    )
    parser.add_argument(
        "--b4",
        type=int,
        default=0,
        help="Blue component for color 4 (4color pattern, default: 0)",
    )

    args = parser.parse_args()
    decklink, bit_depth, devices = setup_decklink_device(args)
    if decklink is None:
        return 1
    
    success = generate_and_display_image(args, decklink, bit_depth)
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
