#!python

# ============================================================================
# Dependencies and Utilities
# ============================================================================

import time

import numpy as np
from numpy.random import rand

from bmd_sg.decklink.bmd_decklink import BMDDeckLink
from bmd_sg.pattern_generator import DEFAULT_PATTERN_GENERATOR
from bmd_sg.utilities import suppress_cpp_output

# ============================================================================
# Device Initialization and Frame Generation
# ============================================================================

# Initialize BMD DeckLink device (device 0)
decklink = BMDDeckLink(0)

# Start the DeckLink device
decklink.start_playback()

# Generate two test frames: white and black
img1 = DEFAULT_PATTERN_GENERATOR.generate(
    [(2081, 2081, 2081)]
)  # White frame (100 nits)
img2 = DEFAULT_PATTERN_GENERATOR.generate([(0, 0, 0)])  # Black frame

# Prime the display with initial frames
decklink.display_frame(img1)
decklink.display_frame(img2)


# ============================================================================
# Performance Testing with Alternating Frame Display
# ============================================================================

# Configuration for performance testing
TARGET_FPS = 30
NUM_FRAME_SEQUENCES = 25  # Number of white/black pairs per test
NUM_TESTS = 15  # Number of test iterations

data = []

# Run performance tests with alternating white/black frame pairs
for _ in range(NUM_TESTS):
    # Suppress C++ library output during frame display
    with suppress_cpp_output():
        t1 = time.perf_counter()
        for _ in range(NUM_FRAME_SEQUENCES):
            decklink.display_frame(img1)  # Show white frame
            decklink.display_frame(img2)  # Show black frame
        t2 = time.perf_counter()

    # Calculate performance metrics
    avg_fps = (NUM_FRAME_SEQUENCES * 2) / (t2 - t1)
    latency_ms = 1000 * (((1 / TARGET_FPS) * (TARGET_FPS - avg_fps)) / avg_fps)
    latency_factor = ((1 / TARGET_FPS) + latency_ms / 1000) / (1 / TARGET_FPS)

    # Store results for statistical analysis
    data += [(avg_fps, latency_ms, latency_factor)]

    # Print per-test results
    print(f"Average Frame Rate: {avg_fps:.4}fps")
    print(f"Latency: {latency_ms:.3}ms")
    print(
        f"Latency: {latency_factor - 1:.03f}frames (Frame update wait time - {latency_factor:0.03f} frames)"
    )

    # Random delay between tests
    time.sleep(rand() * 0.5 + 0.5)


# ============================================================================
# Statistical Summary
# ============================================================================

# Convert to numpy array for statistical analysis
data = np.asarray(data)
latency_ms = data[:, 1]
latency_factor = data[:, 2]

# Calculate statistics for latency in milliseconds
latency_ms_avg = np.mean(latency_ms)
latency_ms_std = np.std(latency_ms)
latency_ms_4sigma = latency_ms_avg + 4 * latency_ms_std

# Calculate statistics for latency factor
latency_factor_avg = np.mean(latency_factor)
latency_factor_std = np.std(latency_factor)
latency_factor_4sigma = latency_factor_avg + 4 * latency_factor_std

# Print comprehensive statistics
print("\n=== Latency Statistics ===")
print("Latency (ms):")
print(f"  Average: {latency_ms_avg:.3f}ms")
print(f"  Std Dev: {latency_ms_std:.3f}ms")
print(f"  +4sigma: {latency_ms_4sigma:.3f}ms")

print("\nLatency Factor (frames):")
print(f"  Average: {latency_factor_avg:.4f}")
print(f"  Std Dev: {latency_factor_std:.4f}")
print(f"  +4sigma: {latency_factor_4sigma:.4f}")
