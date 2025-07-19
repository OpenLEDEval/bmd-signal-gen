# Image Generators Module Development Guide

## Core Principles

**NumPy-Based Algorithms**: Use vectorized operations, no Python loops
```python
y_coords, x_coords = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
checker_indices = ((y_coords // block_size) + (x_coords // block_size)) % len(colors)
array[checker_indices == i] = color
```

**ROI Pattern**: Apply to slice `frame[roi.y:roi.y + roi.height, roi.x:roi.x + roi.width]`

## Color Management

**Bit-Depth Validation**: `max_value = (2 ** bit_depth) - 1`, raise `ColorRangeError` if exceeded
**Color Expansion**: 1 color (solid) → 2 colors (checkerboard) → 3 colors (repeat first) → 4 colors (true 2x2)

## PatternGenerator Structure

```python
class PatternGenerator:
    def __init__(self, width=1920, height=1080, bit_depth=12, roi=None):
        self.bit_depth = bit_depth
        self.max_value = (2 ** bit_depth) - 1
        self.roi = roi or ROI(0, 0, width, height)
```

## Performance Optimization

**Memory efficiency**: Use `np.ascontiguousarray()` and buffer reuse  
**Real-time**: Pre-allocate buffers, avoid repeated allocation  
**Vectorization**: Use NumPy operations instead of loops