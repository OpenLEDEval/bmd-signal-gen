#!/usr/bin/env python3
"""
Four Pattern Demo Script

Generates and displays four different test patterns using the BMD signal generator:
1. Red/Green/Blue/White checkerboard
2. Solid white pattern (100 nits)
3. Color bars pattern
4. Black/White checkerboard

Uses the default PatternGenerator and BMDDeckLink for pattern creation and display.
"""

import time

import numpy as np

from bmd_sg.decklink.bmd_decklink import BMDDeckLink
from bmd_sg.pattern_generator import DEFAULT_PATTERN_GENERATOR
from bmd_sg.utilities import suppress_cpp_output


def generate_four_patterns() -> list[np.ndarray]:
    """Generate four different test patterns using the default generator.

    Returns
    -------
    List[np.ndarray]
        List of four pattern arrays ready for display.
    """
    patterns = []

    # Pattern 1: Red/Green/Blue/White checkerboard (12-bit values)
    # Using 80% values for each color to avoid clipping
    red = [3276, 0, 0]  # 80% red
    green = [0, 3276, 0]  # 80% green
    blue = [0, 0, 3276]  # 80% blue
    white = [3276, 3276, 3276]  # 80% white
    pattern1 = DEFAULT_PATTERN_GENERATOR.generate([red, green, blue, white])
    patterns.append(pattern1)

    # Pattern 2: Solid white (100 nits equivalent)
    white_100nits = [2081, 2081, 2081]  # 100 nits in 12-bit
    pattern2 = DEFAULT_PATTERN_GENERATOR.generate([white_100nits])
    patterns.append(pattern2)

    # Pattern 3: Color bars pattern (SMPTE-style colors)
    # Creating a 2x2 pattern with primary/secondary colors
    cyan = [0, 3276, 3276]  # Cyan
    magenta = [3276, 0, 3276]  # Magenta
    yellow = [3276, 3276, 0]  # Yellow
    black = [0, 0, 0]  # Black
    pattern3 = DEFAULT_PATTERN_GENERATOR.generate([cyan, magenta, yellow, black])
    patterns.append(pattern3)

    # Pattern 4: High contrast black/white checkerboard
    pure_white = [4095, 4095, 4095]  # Maximum 12-bit white
    pure_black = [0, 0, 0]  # Pure black
    pattern4 = DEFAULT_PATTERN_GENERATOR.generate(
        [pure_white, pure_black, pure_black, pure_white]
    )
    patterns.append(pattern4)

    return patterns


def display_patterns_sequence(
    decklink: BMDDeckLink, patterns: list[np.ndarray], display_duration: float = 9.0
) -> None:
    """Display patterns in sequence with timing information.

    Parameters
    ----------
    decklink : BMDDeckLink
        DeckLink device for pattern display.
    patterns : List[np.ndarray]
        List of pattern arrays to display.
    display_duration : float, optional
        Duration to display each pattern in seconds. Default is 2.0.
    """
    pattern_names = [
        "Red/Green/Blue/White Checkerboard",
        "Solid White (100 nits)",
        "Color Bars (Cyan/Magenta/Yellow/Black)",
        "High Contrast Black/White Checkerboard",
    ]

    print(f"Displaying {len(patterns)} patterns, {display_duration}s each...")
    print("=" * 50)

    for i, (pattern, name) in enumerate(zip(patterns, pattern_names, strict=False), 1):
        print(f"Pattern {i}: {name}")

        # Display the pattern
        with suppress_cpp_output():
            start_time = time.perf_counter()
            decklink.display_frame(pattern)
            display_time = time.perf_counter() - start_time

        print(f"  Display time: {display_time * 1000:.2f}ms")
        print(f"  Pattern shape: {pattern.shape}")
        print(f"  Data type: {pattern.dtype}")
        print(f"  Value range: [{pattern.min()}-{pattern.max()}]")

        # Wait for display duration
        time.sleep(display_duration)
        print()


def main() -> None:
    """Main execution function for the four pattern demo."""
    print("BMD Signal Generator - Four Pattern Demo")
    print("=======================================")

    try:
        # Initialize DeckLink device
        print("Initializing DeckLink device 0...")
        decklink = BMDDeckLink(0)

        # Start DeckLink output
        print("Starting DeckLink output...")
        decklink.start()

        # Generate all patterns
        print("Generating patterns...")
        patterns = generate_four_patterns()
        print(f"Generated {len(patterns)} patterns successfully.")
        print()

        # Display patterns in sequence
        display_patterns_sequence(decklink, patterns, display_duration=3)

        print("Demo completed successfully!")

    except Exception as e:
        print(f"Error during demo: {e}")
        raise
    finally:
        # Clean up would go here if needed
        print("Demo finished.")


if __name__ == "__main__":
    main()
