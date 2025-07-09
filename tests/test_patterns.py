import numpy as np
import pytest  # type: ignore # pytest must be installed for these tests

from bmd_signals.patterns import ColorValidator, PatternGenerator, PatternType


# --- PatternType Enum ---
def test_pattern_type_enum():
    assert PatternType.SOLID.value == "solid"
    assert PatternType.TWO_COLOR.value == "2color"
    assert PatternType.FOUR_COLOR.value == "4color"


# --- ColorValidator ---
def test_color_validator_valid():
    for bit_depth, max_val in [(8, 255), (10, 1023), (12, 4095)]:
        v = ColorValidator(bit_depth)
        v.validate_color(0, 0, 0)
        v.validate_color(max_val, max_val, max_val)
        v.validate_color_tuple((max_val, 0, 0))


@pytest.mark.parametrize("bit_depth,max_val", [(8, 255), (10, 1023), (12, 4095)])
def test_color_validator_invalid(bit_depth, max_val):
    v = ColorValidator(bit_depth)
    with pytest.raises(ValueError):
        v.validate_color(max_val + 1, 0, 0)
    with pytest.raises(ValueError):
        v.validate_color(0, max_val + 1, 0)
    with pytest.raises(ValueError):
        v.validate_color(0, 0, max_val + 1)
    with pytest.raises(ValueError):
        v.validate_color(-1, 0, 0)
    with pytest.raises(ValueError):
        v.validate_color_tuple((0, 0))  # type: ignore  # Intentionally wrong tuple size for error test


# --- PatternGenerator ---
def test_generate_solid():
    gen = PatternGenerator(4, 4, 12, PatternType.SOLID)
    arr = gen.generate((100, 200, 300))
    assert arr.shape == (4, 4, 3)
    assert np.all(arr[:, :, 0] == 100)
    assert np.all(arr[:, :, 1] == 200)
    assert np.all(arr[:, :, 2] == 300)


def test_generate_2color():
    gen = PatternGenerator(2, 2, 12, PatternType.TWO_COLOR)
    arr = gen.generate((100, 0, 0), (0, 200, 0))
    # Checkerboard: [A, B; B, A]
    assert arr[0, 0, 0] == 100 and arr[0, 0, 1] == 0
    assert arr[0, 1, 1] == 200 and arr[0, 1, 0] == 0
    assert arr[1, 0, 1] == 200 and arr[1, 0, 0] == 0
    assert arr[1, 1, 0] == 100 and arr[1, 1, 1] == 0


def test_generate_4color():
    gen = PatternGenerator(2, 2, 12, PatternType.FOUR_COLOR)
    arr = gen.generate((1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12))
    # Pattern: [A, B; C, D]
    assert tuple(arr[0, 0]) == (1, 2, 3)
    assert tuple(arr[0, 1]) == (4, 5, 6)
    assert tuple(arr[1, 0]) == (7, 8, 9)
    assert tuple(arr[1, 1]) == (10, 11, 12)
