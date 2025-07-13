#!/usr/bin/env python3
"""
Simple Four Pattern Demo - Quick Example

Displays four different test patterns in sequence using BMD DeckLink.
No functions - just a straightforward linear script.
"""

import time

from bmd_sg.decklink.bmd_decklink import BMDDeckLink
from bmd_sg.pattern_generator import DEFAULT_PATTERN_GENERATOR

# Initialize DeckLink device 0
decklink = BMDDeckLink(0)
decklink.start_playback()

# Pattern 1: Red/Green/Blue/White checkerboard
print("Pattern 1: Red/Green/Blue/White Checkerboard")
colors = [
    (2000, 0, 0),
    (0000, 0, 0),
    (0000, 2000, 0),
    (0000, 0, 0),
]
pattern1 = DEFAULT_PATTERN_GENERATOR.generate(colors)
decklink.display_frame(pattern1)
time.sleep(3)

# Pattern 2: Solid white (100 nits)
print("Pattern 2: Solid White (100 nits)")
white_100nits = [2081, 2081, 2081]
pattern2 = DEFAULT_PATTERN_GENERATOR.generate([white_100nits])
decklink.display_frame(pattern2)
time.sleep(3)

# Pattern 3: Color bars (Cyan/Magenta/Yellow/Black)
print("Pattern 3: Color Bars")
cyan = [0, 3276, 3276]
magenta = [3276, 0, 3276]
yellow = [3276, 3276, 0]
black = [0, 0, 0]
pattern3 = DEFAULT_PATTERN_GENERATOR.generate([cyan, magenta, yellow, black])
decklink.display_frame(pattern3)
time.sleep(3)

# Pattern 4: High contrast black/white checkerboard
print("Pattern 4: High Contrast Black/White")
pure_white = [4095, 4095, 4095]
pure_black = [0, 0, 0]
pattern4 = DEFAULT_PATTERN_GENERATOR.generate([pure_white, pure_black])
decklink.display_frame(pattern4)
time.sleep(3)

print("Demo complete!")
decklink.close()
