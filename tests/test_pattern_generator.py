"""
Tests for PatternGenerator and color validation.

This module tests the pattern generation functionality including
checkerboard pattern creation, color validation, and ROI handling.
"""

import numpy as np
import pytest

from bmd_sg.image_generators.checkerboard import (
    ROI,
    ColorRangeError,
    PatternGenerator,
)


class TestPatternGenerator:
    """Tests for the PatternGenerator class."""

    def test_generate_single_color(
        self, pattern_generator_12bit: PatternGenerator
    ) -> None:
        """Test generating a pattern with a single solid color."""
        colors = [[2048, 2048, 2048]]  # Mid-gray
        pattern = pattern_generator_12bit.generate(colors)

        assert pattern is not None
        assert pattern.shape == (1080, 1920, 3)
        assert pattern.dtype == np.uint16

    def test_generate_two_colors(
        self, pattern_generator_12bit: PatternGenerator
    ) -> None:
        """Test generating a checkerboard with two colors."""
        colors = [[4095, 4095, 4095], [0, 0, 0]]  # White and black
        pattern = pattern_generator_12bit.generate(colors)

        assert pattern is not None
        assert pattern.shape == (1080, 1920, 3)

    def test_generate_four_colors(
        self,
        pattern_generator_12bit: PatternGenerator,
        sample_colors_12bit: list[list[int]],
    ) -> None:
        """Test generating a checkerboard with four colors."""
        pattern = pattern_generator_12bit.generate(sample_colors_12bit)

        assert pattern is not None
        assert pattern.shape == (1080, 1920, 3)

    def test_color_out_of_range_raises_error(
        self, pattern_generator_12bit: PatternGenerator
    ) -> None:
        """Test that out-of-range colors raise ColorRangeError."""
        invalid_colors = [[5000, 0, 0]]  # Exceeds 12-bit max (4095)

        with pytest.raises(ColorRangeError):
            pattern_generator_12bit.generate(invalid_colors)

    def test_negative_color_raises_error(
        self, pattern_generator_12bit: PatternGenerator
    ) -> None:
        """Test that negative color values raise ColorRangeError."""
        invalid_colors = [[-1, 0, 0]]

        with pytest.raises(ColorRangeError):
            pattern_generator_12bit.generate(invalid_colors)

    def test_8bit_color_range(self, pattern_generator_8bit: PatternGenerator) -> None:
        """Test 8-bit color range validation."""
        valid_colors = [[255, 128, 0]]
        pattern = pattern_generator_8bit.generate(valid_colors)

        assert pattern is not None
        assert pattern.dtype == np.uint16  # Internal representation

    def test_8bit_out_of_range_raises_error(
        self, pattern_generator_8bit: PatternGenerator
    ) -> None:
        """Test that 8-bit out-of-range colors raise ColorRangeError."""
        invalid_colors = [[256, 0, 0]]  # Exceeds 8-bit max (255)

        with pytest.raises(ColorRangeError):
            pattern_generator_8bit.generate(invalid_colors)


class TestROI:
    """Tests for the ROI (Region of Interest) class."""

    def test_roi_creation(self) -> None:
        """Test basic ROI creation."""
        roi = ROI(x=100, y=100, width=800, height=600)

        assert roi.x == 100
        assert roi.y == 100
        assert roi.width == 800
        assert roi.height == 600

    def test_roi_x2_property(self) -> None:
        """Test ROI x2 property (right edge)."""
        roi = ROI(x=100, y=100, width=800, height=600)

        assert roi.x2 == 900  # 100 + 800

    def test_roi_y2_property(self) -> None:
        """Test ROI y2 property (bottom edge)."""
        roi = ROI(x=100, y=100, width=800, height=600)

        assert roi.y2 == 700  # 100 + 600

    def test_roi_default_values(self) -> None:
        """Test ROI default values."""
        roi = ROI()

        assert roi.x == 0
        assert roi.y == 0
        assert roi.width == 100
        assert roi.height == 100

    def test_pattern_with_roi(self) -> None:
        """Test pattern generation with custom ROI."""
        roi = ROI(x=100, y=100, width=400, height=300)
        generator = PatternGenerator(
            bit_depth=12,
            width=1920,
            height=1080,
            roi=roi,
        )

        pattern = generator.generate([[4095, 0, 0]])

        assert pattern is not None
        assert pattern.shape == (1080, 1920, 3)


class TestColorRangeError:
    """Tests for the ColorRangeError exception."""

    def test_error_message(self) -> None:
        """Test that ColorRangeError has appropriate message."""
        error = ColorRangeError()

        assert "bit-depth range" in str(error)

    def test_error_with_detail(self) -> None:
        """Test ColorRangeError with detail string."""
        error = ColorRangeError("Value 5000 exceeds 12-bit max 4095")

        # The detail is added as a note, not part of the main message
        assert len(error.__notes__) == 1
        assert "5000" in error.__notes__[0]
