#!/usr/bin/env python3
"""
Demo script showing how to use mock DeckLink devices for testing.

This script demonstrates using the mock infrastructure to test
BMD Signal Generator functionality without physical hardware.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from bmd_sg.decklink.bmd_decklink import (
    EOTFType,
    HDRMetadata,
    PixelFormatType,
)
from bmd_sg.image_generators.checkerboard import PatternGenerator
from tests.mocks.mock_decklink import (
    MockBMDDeckLink,
    mock_get_decklink_devices,
    patch_decklink_module,
    reset_mock_state,
    set_available_devices,
)


def demo_basic_mock_usage():
    """Demonstrate basic mock device usage."""
    print("=== Basic Mock Usage ===")

    # Create a mock device directly
    device = MockBMDDeckLink(0)
    print(f"Created mock device at index {device.device_index}")
    print(f"Device name: {device.device_name}")
    print(f"Device is open: {device.is_open}")

    # Start playback
    device.start_playback()
    print(f"Playback started: {device.started}")

    # Set pixel format
    device.pixel_format = PixelFormatType.FORMAT_12BIT_RGB
    print(f"Pixel format set to: {device.pixel_format}")

    # Display a frame
    frame = np.zeros((1080, 1920, 3), dtype=np.uint16)
    device.display_frame(frame)
    print("Frame displayed")

    # Check method calls
    calls = device.get_method_calls()
    print("\nMethod calls tracked:")
    for method, call_list in calls.items():
        if call_list:
            print(f"  {method}: {len(call_list)} calls")

    # Cleanup
    device.close()
    print("\nDevice closed")


def demo_cli_integration():
    """Demonstrate using mocks with CLI functions."""
    print("\n=== CLI Integration Demo ===")

    # Reset and configure mock environment
    reset_mock_state()
    set_available_devices(
        [
            "Mock DeckLink 8K Pro",
            "Mock DeckLink Mini Monitor 4K",
            "Mock DeckLink Studio 4K",
        ]
    )

    with patch_decklink_module():
        # List devices using CLI function
        print("Available devices:")
        devices = mock_get_decklink_devices()
        for i, device in enumerate(devices):
            print(f"  {i}: {device}")

        # Create device directly to avoid complex initialization
        print("\nCreating device 1...")
        device = MockBMDDeckLink(1)
        device.pixel_format = PixelFormatType.FORMAT_12BIT_RGB
        device.start_playback()

        print(f"Device initialized: {device.device_name}")
        print(f"Pixel format: {device.pixel_format}")
        print(f"HDR support: {device.supports_hdr}")

        # Configure HDR
        metadata = HDRMetadata(
            eotf=EOTFType.PQ,
            max_cll=4000.0,
        )
        device.set_hdr_metadata(metadata)
        print("✓ HDR metadata configured")

        # Verify it's a mock
        assert isinstance(device, MockBMDDeckLink)
        print("✓ Confirmed using mock device")

        device.close()


def demo_pattern_generation():
    """Demonstrate pattern generation with mocks."""
    print("\n=== Pattern Generation Demo ===")

    with patch_decklink_module():
        # Create device and generator
        device = MockBMDDeckLink(0)
        device.pixel_format = PixelFormatType.FORMAT_12BIT_RGB
        device.start_playback()

        generator = PatternGenerator(
            bit_depth=12,
            width=1920,
            height=1080,
        )

        # Generate various patterns
        patterns = [
            ("Solid Red", [[4095, 0, 0]]),
            ("Red/Black Checkerboard", [[4095, 0, 0], [0, 0, 0]]),
            ("RGB Checkerboard", [[4095, 0, 0], [0, 4095, 0], [0, 0, 4095]]),
            ("Four Color", [[4095, 0, 0], [0, 4095, 0], [0, 0, 4095], [4095, 4095, 0]]),
        ]

        for name, colors in patterns:
            print(f"\nGenerating {name}...")
            pattern = generator.generate(colors)
            device.display_frame(pattern)
            print(f"  Pattern shape: {pattern.shape}")
            print(f"  Pattern dtype: {pattern.dtype}")

        # Check frame history
        frames = device.get_frame_history()
        print(f"\nTotal frames displayed: {len(frames)}")

        # Examine last frame
        last_frame = device.get_last_frame()
        if last_frame is not None:
            print(f"Last frame shape: {last_frame.shape}")
            print(
                f"Last frame mean values: R={last_frame[:, :, 0].mean():.1f}, "
                f"G={last_frame[:, :, 1].mean():.1f}, B={last_frame[:, :, 2].mean():.1f}"
            )

        device.close()


def demo_hdr_configuration():
    """Demonstrate HDR configuration with mocks."""
    print("\n=== HDR Configuration Demo ===")

    device = MockBMDDeckLink(0)
    device.pixel_format = PixelFormatType.FORMAT_12BIT_RGB

    # Configure HDR metadata
    metadata = HDRMetadata(
        eotf=EOTFType.PQ,
        max_display_luminance=1000.0,
        min_display_luminance=0.0001,
        max_cll=4000.0,
        max_fall=400.0,
    )

    print(f"HDR Support: {device.supports_hdr}")
    print("Setting HDR metadata:")
    print(f"  EOTF: {EOTFType.PQ}")
    print(f"  MaxCLL: {metadata.maxCLL} cd/m²")
    print(f"  MaxFALL: {metadata.maxFALL} cd/m²")

    device.set_hdr_metadata(metadata)

    # Verify HDR was set
    hdr_calls = device.get_method_calls("set_hdr_metadata")
    if hdr_calls:
        print("✓ HDR metadata configured successfully")
        set_metadata = hdr_calls[0]["metadata"]
        print(f"  Verified EOTF value: {set_metadata.EOTF}")

    device.close()


def demo_error_conditions():
    """Demonstrate testing error conditions."""
    print("\n=== Error Conditions Demo ===")

    # Test invalid device index
    print("Testing invalid device index...")
    reset_mock_state()
    set_available_devices(["Device 0"])  # Only one device

    try:
        device = MockBMDDeckLink(1)  # Try to open second device
    except RuntimeError as e:
        print(f"✓ Expected error: {e}")

    # Test operations on closed device
    print("\nTesting operations on closed device...")
    device = MockBMDDeckLink(0)
    device.close()

    try:
        device.start_playback()
    except RuntimeError as e:
        print(f"✓ Expected error: {e}")

    # Test unsupported pixel format
    print("\nTesting unsupported pixel format...")
    device = MockBMDDeckLink(0)

    try:
        device.pixel_format = PixelFormatType.FORMAT_H265
    except RuntimeError as e:
        print(f"✓ Expected error: {e}")

    device.close()


def demo_verification_features():
    """Demonstrate mock verification features."""
    print("\n=== Verification Features Demo ===")

    device = MockBMDDeckLink(0)

    # Perform various operations
    device.start_playback()
    device.pixel_format = PixelFormatType.FORMAT_10BIT_RGB
    frame1 = np.full((100, 100, 3), 1000, dtype=np.uint16)
    frame2 = np.full((100, 100, 3), 2000, dtype=np.uint16)
    device.display_frame(frame1)
    device.display_frame(frame2)
    device.stop_playback()

    # Detailed method tracking
    print("Method call details:")
    print(f"  start_playback: {device.get_method_calls('start_playback')}")
    print(f"  set_pixel_format: {device.get_method_calls('set_pixel_format')}")
    print(f"  display_frame: {device.get_method_calls('display_frame')}")

    # Frame history analysis
    frames = device.get_frame_history()
    print(f"\nFrame history ({len(frames)} frames):")
    for i, frame in enumerate(frames):
        print(f"  Frame {i}: mean={frame.mean():.1f}, shape={frame.shape}")

    # Clear history
    device.clear_history()
    print("\nHistory cleared")
    print(
        f"  Method calls after clear: {len(device.get_method_calls('display_frame'))}"
    )
    print(f"  Frame history after clear: {len(device.get_frame_history())}")

    device.close()


def main():
    """Run all demos."""
    print("BMD Signal Generator Mock Testing Demo")
    print("=" * 50)

    demos = [
        demo_basic_mock_usage,
        demo_cli_integration,
        demo_pattern_generation,
        demo_hdr_configuration,
        demo_error_conditions,
        demo_verification_features,
    ]

    for demo in demos:
        demo()
        print()

    print("Demo complete!")
    print("\nKey Takeaways:")
    print("- Mock devices behave like real devices but track all operations")
    print("- Use patch_decklink_module() to replace real devices with mocks")
    print("- Method calls and frames are tracked for verification")
    print("- Error conditions can be simulated for robust testing")
    print("- Perfect for CI/CD pipelines and development without hardware")


if __name__ == "__main__":
    main()
