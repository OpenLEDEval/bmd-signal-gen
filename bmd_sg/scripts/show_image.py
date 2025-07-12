import contextlib
import time

from numpy.random import rand

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


for _ in range(10):
    NUM = 10
    with contextlib.redirect_stdout(open("/dev/null", "w")):
        t1 = time.perf_counter()
        for i in range(NUM):
            decklink.display_frame(img1)
            decklink.display_frame(img2)
        t2 = time.perf_counter()

    print(f"Average Frame Rate: {(NUM * 2) / (t2 - t1):.4}fps")

    target = 30
    avg = (NUM * 2) / (t2 - t1)

    print(f"Latency: {1000 * (((1 / target) * (target - avg)) / avg):.3}ms")
    time.sleep(rand() * 2 + 1)
