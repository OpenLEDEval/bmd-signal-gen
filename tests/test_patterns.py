import numpy as np

from bmd_sg.image_generators.checkerboard import ROI, PatternGenerator


def test_pattern_generator_single_color():
    """Test PatternGenerator with a single color."""
    gen = PatternGenerator(bit_depth=8, width=4, height=4)
    pattern = gen.generate([255, 0, 0])  # Red
    assert pattern.shape == (4, 4, 3)
    # Single color should fill entire pattern
    assert np.all(pattern[:, :, 0] == 255)
    assert np.all(pattern[:, :, 1] == 0)
    assert np.all(pattern[:, :, 2] == 0)


def test_pattern_generator_two_colors():
    """Test PatternGenerator with two colors creating checkerboard."""
    gen = PatternGenerator(bit_depth=8, width=4, height=4)
    pattern = gen.generate([[255, 0, 0], [0, 255, 0]])  # Red and Green
    assert pattern.shape == (4, 4, 3)
    # Should create alternating pattern


def test_roi_properties():
    """Test ROI properties and calculations."""
    roi = ROI(x=10, y=20, width=100, height=200)
    assert roi.x == 10
    assert roi.y == 20
    assert roi.width == 100
    assert roi.height == 200
    assert roi.x2 == 110  # x + width
    assert roi.y2 == 220  # y + height


def test_pattern_generator_with_roi():
    """Test PatternGenerator with a custom ROI."""
    roi = ROI(x=1, y=1, width=2, height=2)
    gen = PatternGenerator(bit_depth=8, width=4, height=4, roi=roi)
    pattern = gen.generate([255, 0, 0])  # Red
    assert pattern.shape == (4, 4, 3)
