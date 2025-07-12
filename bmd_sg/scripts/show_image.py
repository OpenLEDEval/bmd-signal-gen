from bmd_sg.decklink.bmd_decklink import BMDDeckLink
from bmd_sg.pattern_generator import PatternGenerator, PatternType

decklink = BMDDeckLink(0)


generator = PatternGenerator(
    width=1920,
    height=1080,
    bit_depth=12,
    pattern_type=PatternType.SOLID,
    roi_x=0,
    roi_y=0,
    roi_width=1920,
    roi_height=1080,
)

decklink.start()

img1 = generator.generate(((2000, 2000, 2000),))
img2 = generator.generate(((0, 0, 0),))
# Generate pattern based on type
for i in range(10):
    decklink.display_frame(img1)
    decklink.display_frame(img2)
