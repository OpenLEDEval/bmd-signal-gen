# Image Generators Module Development Guide

## Core Principles

### NumPy-Based Algorithms
Use vectorized operations, no Python loops:
```python
# Create coordinate grids and use advanced indexing
y_coords, x_coords = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
checker_indices = ((y_coords // block_size) + (x_coords // block_size)) % len(colors)
array[checker_indices == i] = color
```

### ROI (Region of Interest)
```python
@dataclass
class ROI:
    x: int = 0
    y: int = 0  
    width: int = 100
    height: int = 100
```

Apply patterns to ROI slice: `frame[roi.y:roi.y + roi.height, roi.x:roi.x + roi.width]`

## Color Management

### Bit-Depth Validation
```python
def validate_color_for_bit_depth(color: list[int], bit_depth: int) -> None:
    max_value = (2 ** bit_depth) - 1
    for component in color:
        if component < 0 or component > max_value:
            raise ColorRangeError(color, bit_depth, max_value)
```

### Color Expansion
- 1 color → solid pattern
- 2 colors → standard checkerboard  
- 3 colors → repeat first for 4th position
- 4 colors → true 2x2 checkerboard

## PatternGenerator Structure

```python
class PatternGenerator:
    def __init__(self, width=1920, height=1080, bit_depth=12, roi=None):
        self.bit_depth = bit_depth
        self.max_value = (2 ** bit_depth) - 1
        self.roi = roi or ROI(0, 0, width, height)
    
    def create_base_frame(self, fill_value=0) -> np.ndarray:
        dtype = np.uint16 if self.bit_depth > 8 else np.uint8
        return np.full((self.height, self.width, 3), fill_value, dtype=dtype)
```

## Performance Optimization

- **Memory efficiency**: Use `np.ascontiguousarray()` and buffer reuse
- **Real-time**: Pre-allocate buffers, avoid repeated allocation
- **Vectorization**: Use NumPy operations instead of loops

Focus on efficient, real-time pattern generation for video applications.