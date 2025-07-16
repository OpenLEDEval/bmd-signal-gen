"""Direct DeckLink API tests for pixel format validation.

This module provides minimal tests that directly exercise the DeckLink API
to isolate R210 scaling issues from the pattern generation layer.
"""

import time

import numpy as np

from bmd_sg.decklink.bmd_decklink import BMDDeckLink, PixelFormatType


def create_solid_color_frame(
    width: int, height: int, rgb_color: tuple[int, int, int]
) -> np.ndarray:
    """Create a numpy array filled with a solid color.

    Parameters
    ----------
    width : int
        Frame width in pixels
    height : int
        Frame height in pixels
    rgb_color : Tuple[int, int, int]
        RGB color values (r, g, b)

    Returns
    -------
    np.ndarray
        Frame array with shape (height, width, 3) filled with the specified color
    """
    frame = np.full((height, width, 3), rgb_color, dtype=np.uint16)
    return frame


def display_color_test(
    device: BMDDeckLink,
    pixel_format: PixelFormatType,
    rgb_color: tuple[int, int, int],
    duration: float = 2.0,
) -> None:
    """Display a solid color for the specified duration.

    Parameters
    ----------
    device : BMDDeckLink
        Configured DeckLink device
    pixel_format : PixelFormatType
        Pixel format to use for display
    rgb_color : Tuple[int, int, int]
        RGB color values appropriate for the pixel format bit depth
    duration : float, optional
        Display duration in seconds, by default 2.0
    """
    # Configure pixel format
    device.pixel_format = pixel_format

    # Create solid color frame
    frame = create_solid_color_frame(1920, 1080, rgb_color)

    # Display frame
    print(f"Displaying {pixel_format} {rgb_color} for {duration}s...")
    device.display_frame(frame)
    time.sleep(duration)


def test_r210_full_scale_colors():
    """Test R210 format with full-scale RGB values.

    This test displays full-scale red, green, and blue using R210 (10-bit) format.
    Full-scale for 10-bit is 1023 (2^10 - 1).
    """
    print("Opening DeckLink device...")
    device = BMDDeckLink(0)  # Device opens automatically in constructor

    try:
        print("Starting playback...")
        device.start_playback()

        # Test full-scale R210 colors
        pixel_format = PixelFormatType.FORMAT_10BIT_RGB

        # Full-scale red (10-bit)
        display_color_test(device, pixel_format, (1023, 0, 0), 2.0)

        # Full-scale green (10-bit)
        display_color_test(device, pixel_format, (0, 1023, 0), 2.0)

        # Full-scale blue (10-bit)
        display_color_test(device, pixel_format, (0, 0, 1023), 2.0)

        # Full-scale white (10-bit)
        display_color_test(device, pixel_format, (1023, 1023, 1023), 2.0)

    finally:
        device.close()


def test_r12l_full_scale_colors():
    """Test R12L format with full-scale RGB values.

    This test displays full-scale red, green, and blue using R12L (12-bit) format.
    Full-scale for 12-bit is 4095 (2^12 - 1).
    """
    print("Opening DeckLink device...")
    device = BMDDeckLink(0)  # Device opens automatically in constructor

    try:
        print("Starting playback...")
        device.start_playback()

        # Test full-scale R12L colors
        pixel_format = PixelFormatType.FORMAT_12BIT_RGBLE

        # Full-scale red (12-bit)
        display_color_test(device, pixel_format, (4095, 0, 0), 2.0)

        # Full-scale green (12-bit)
        display_color_test(device, pixel_format, (0, 4095, 0), 2.0)

        # Full-scale blue (12-bit)
        display_color_test(device, pixel_format, (0, 0, 4095), 2.0)

        # Full-scale white (12-bit)
        display_color_test(device, pixel_format, (4095, 4095, 4095), 2.0)

    finally:
        device.close()


def test_equivalent_gray_levels():
    """Test that equivalent gray levels produce same brightness.

    This test compares mid-scale gray values between R210 and R12L formats.
    50% gray should appear the same brightness in both formats.
    """
    print("Opening DeckLink device...")
    device = BMDDeckLink(0)  # Device opens automatically in constructor

    try:
        print("Starting playback...")
        device.start_playback()

        # Test R210 50% gray (512 out of 1023)
        print("\nTesting R210 50% gray...")
        display_color_test(
            device, PixelFormatType.FORMAT_10BIT_RGB, (512, 512, 512), 3.0
        )

        # Test R12L 50% gray (2048 out of 4095)
        print("\nTesting R12L 50% gray...")
        display_color_test(
            device, PixelFormatType.FORMAT_12BIT_RGBLE, (2048, 2048, 2048), 3.0
        )

        # Test R210 25% gray (256 out of 1023)
        print("\nTesting R210 25% gray...")
        display_color_test(
            device, PixelFormatType.FORMAT_10BIT_RGB, (256, 256, 256), 3.0
        )

        # Test R12L 25% gray (1024 out of 4095)
        print("\nTesting R12L 25% gray...")
        display_color_test(
            device, PixelFormatType.FORMAT_12BIT_RGBLE, (1024, 1024, 1024), 3.0
        )

    finally:
        device.close()


def test_r210_scaling_investigation():
    """Investigate R210 scaling by testing multiple brightness levels.

    This test displays a range of brightness levels in R210 format
    to determine if there's a scaling issue.
    """
    print("Opening DeckLink device...")
    device = BMDDeckLink(0)  # Device opens automatically in constructor

    try:
        print("Starting playback...")
        device.start_playback()

        pixel_format = PixelFormatType.FORMAT_10BIT_RGB

        # Test various brightness levels
        test_levels = [
            (0, "Black (0%)"),
            (102, "10% Gray"),
            (256, "25% Gray"),
            (512, "50% Gray"),
            (768, "75% Gray"),
            (921, "90% Gray"),
            (1023, "100% White"),
        ]

        for level, description in test_levels:
            print(f"\nTesting R210 {description}: ({level}, {level}, {level})")
            display_color_test(device, pixel_format, (level, level, level), 2.0)

    finally:
        device.close()


def run_all_tests():
    """Run all DeckLink tests in sequence with user prompts."""
    print("=== DeckLink R210 vs R12L Scaling Tests ===")
    print("This test will display various colors and brightness levels")
    print("to compare R210 (10-bit) and R12L (12-bit) pixel formats.\n")

    input("Press Enter to start R210 full-scale color tests...")
    test_r210_full_scale_colors()

    input("\nPress Enter to start R12L full-scale color tests...")
    test_r12l_full_scale_colors()

    input("\nPress Enter to start equivalent gray level comparison...")
    test_equivalent_gray_levels()

    input("\nPress Enter to start R210 scaling investigation...")
    test_r210_scaling_investigation()

    print("\n=== Tests Complete ===")
    print("Compare the brightness levels between R210 and R12L formats.")
    print("If R210 appears dimmer than expected, the issue is in the DeckLink wrapper.")


if __name__ == "__main__":
    run_all_tests()
