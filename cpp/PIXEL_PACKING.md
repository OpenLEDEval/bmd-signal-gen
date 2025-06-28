# Pixel Packing Implementation Documentation

## Overview

This document describes the pixel packing schemes implemented for Blackmagic DeckLink devices. The implementation has been refactored into separate files for better organization and maintainability.

**Important Note**: The current implementation does NOT perform any scaling or color space conversion. All functions expect input values in the correct bit depth range for the target format.

**API Consistency**: All functions follow a consistent frame-filling API pattern, where each function fills an entire frame buffer with the specified color.

## File Structure

- `pixel_packing.h` - Header file with function declarations and documentation
- `pixel_packing.cpp` - Implementation of all pixel packing functions
- `decklink_wrapper.cpp` - Main wrapper that uses the pixel packing functions

## Input Requirements

### Bit Depth Expectations
- **8-bit functions**: Expect 8-bit values (0-255)
- **10-bit functions**: Expect 10-bit values (0-1023)
- **12-bit function**: Expect 12-bit values (0-4095)

### No Automatic Scaling
The current implementation does not perform any automatic scaling between bit depths. If you need to convert from 8-bit to 10-bit or 12-bit, you must perform the scaling before calling these functions.

**Example scaling formulas:**
- 8-bit to 10-bit: `value_10bit = (value_8bit * 1023) / 255`
- 8-bit to 12-bit: `value_12bit = (value_8bit * 4095) / 255`

## Supported Pixel Formats

### 1. 8-bit RGB Formats

#### BGRA Format (`bmdFormat8BitBGRA`)
- **Structure**: 32-bit word with alpha channel
- **Byte Order**: AABBGGRR (Alpha, Blue, Green, Red)
- **Alpha**: Set to 0xFF (fully opaque)
- **Input Range**: 0-255 for each RGB channel
- **Function**: `fill_8bit_rgb_frame(frameData, width, height, rowBytes, r, g, b, true)`

#### ARGB Format (`bmdFormat8BitARGB`)
- **Structure**: 32-bit word with alpha channel
- **Byte Order**: AARRGGBB (Alpha, Red, Green, Blue)
- **Alpha**: Set to 0xFF (fully opaque)
- **Input Range**: 0-255 for each RGB channel
- **Function**: `fill_8bit_rgb_frame(frameData, width, height, rowBytes, r, g, b, false)`

### 2. 10-bit RGB Format (`bmdFormat10BitRGB`)

#### Direct Packing (No Scaling)
- **Input**: 10-bit RGB values (0-1023) - NO SCALING PERFORMED
- **Output**: 10-bit RGB values packed into 32-bit words, filling entire frame
- **Method**: Direct packing without bit replication or scaling

#### Packing Structure
- **Bits 0-9**: Blue channel (10 bits)
- **Bits 10-19**: Green channel (10 bits)
- **Bits 20-29**: Red channel (10 bits)
- **Bits 30-31**: Unused (padding)
- **Function**: `fill_10bit_rgb_frame(frameData, width, height, rowBytes, r, g, b)`

### 3. 10-bit YUV Format (`bmdFormat10BitYUV`)

#### Direct YUV Packing (No Color Space Conversion)
- **Input**: 10-bit YUV values (0-1023) - NO COLOR SPACE CONVERSION PERFORMED
- **Output**: 10-bit YUV values packed into 32-bit words, filling entire frame
- **Method**: Direct packing of YUV values

#### Packing Structure
- **Bits 0-9**: U channel (10 bits)
- **Bits 10-19**: Y channel (10 bits)
- **Bits 20-29**: V channel (10 bits)
- **Bits 30-31**: Unused (padding)
- **Function**: `fill_10bit_yuv_frame(frameData, width, height, rowBytes, y, u, v)`

**Note**: If you need RGB to YUV conversion, you must perform it before calling this function using the BT.709 matrix:

```
Y = 0.2126*R + 0.7152*G + 0.0722*B
U = -0.1146*R - 0.3854*G + 0.5000*B
V = 0.5000*R - 0.4542*G - 0.0458*B
```

### 4. 12-bit RGB Format (`bmdFormat12BitRGB`) - REFACTORED

#### Complex Interleaved Packing Scheme (Refactored)

This is the most complex format, requiring special handling due to the interleaved packing scheme used by Blackmagic DeckLink devices. The implementation has been **refactored** to provide a clear structure for defining the correct pixel interleaving pattern.

##### Direct 12-bit Input (No Scaling)
- **Input**: 12-bit RGB values (0-4095) - NO SCALING PERFORMED
- **Output**: Interleaved 12-bit RGB data filling entire frame
- **Method**: Direct packing without scaling

##### Channel Splitting
Each 12-bit RGB channel is split into two parts:
- **Low 8 bits**: Channel[7:0] (stored in separate bytes)
- **High 4 bits**: Channel[11:8] (packed into combined bytes)

##### Memory Layout (Refactored)
- **Per Pixel**: 36 bits (4.5 bytes)
- **Per Group**: 8 pixels fit into 36 bytes (288 bits total)
- **Row Alignment**: Follows DeckLink API requirements
- **Processing**: Uses `pack_8_pixels_into_36_bytes()` helper function

##### Refactored Implementation Structure

The 12-bit RGB packing has been refactored to provide a clear structure for customization:

```cpp
// Helper function for 8-pixel interleaving
static void pack_8_pixels_into_36_bytes(uint8_t* groupPtr, 
                                       const uint8_t r_low[8], const uint8_t r_high[8],
                                       const uint8_t g_low[8], const uint8_t g_high[8], 
                                       const uint8_t b_low[8], const uint8_t b_high[8]);
```

##### Customization Points

The refactored implementation provides several customization points:

1. **Main Function**: `fill_12bit_rgb_frame()` - Handles frame-level processing
2. **Helper Function**: `pack_8_pixels_into_36_bytes()` - Handles 8-pixel interleaving
3. **Input Arrays**: Separate arrays for each channel's low and high bits
4. **Pattern Definition**: Clear structure for defining interleaving patterns

##### Current Placeholder Pattern

The current implementation uses a placeholder pattern that needs to be customized:

```cpp
// CURRENT PLACEHOLDER: Simple sequential packing
for (int pixel = 0; pixel < 8; pixel++) {
    int baseByte = pixel * 4; // Integer part of 4.5
    
    groupPtr[baseByte] = r_low[pixel];      // Byte 0: R_low[7:0]
    groupPtr[baseByte + 1] = g_low[pixel];  // Byte 1: G_low[7:0]
    groupPtr[baseByte + 2] = b_low[pixel];  // Byte 2: B_low[7:0]
    groupPtr[baseByte + 3] = r_high[pixel] | (g_high[pixel] << 4); // Byte 3: Combined
    groupPtr[baseByte + 4] = b_high[pixel]; // Byte 4: B_high[3:0]
}
```

##### Alternative Pattern Examples

The implementation includes commented examples of alternative patterns:

1. **Interleaved Pattern**: Alternates between 8-bit low and 4-bit high components
2. **Planar Pattern**: Groups all low bits together, then all high bits
3. **Custom Pattern**: Based on specific hardware requirements

##### Function
- **Function**: `fill_12bit_rgb_frame(frameData, width, height, rowBytes, r, g, b)`

## Implementation Details

### Function Signatures

```cpp
// 8-bit RGB frame filling
void fill_8bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes,
                        uint8_t r, uint8_t g, uint8_t b, bool isBGRA = true);

// 10-bit RGB frame filling (expects 10-bit values)
void fill_10bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes,
                         uint16_t r, uint16_t g, uint16_t b);

// 10-bit YUV frame filling (expects 10-bit YUV values)
void fill_10bit_yuv_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes,
                         uint16_t y, uint16_t u, uint16_t v);

// 12-bit RGB frame filling (expects 12-bit values) - REFACTORED
void fill_12bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes, 
                         uint16_t r, uint16_t g, uint16_t b);
```

### Range Checking
All functions include automatic range checking and will clamp values to the valid range for their respective bit depth:
- 8-bit functions: Clamp to 0-255
- 10-bit functions: Clamp to 0-1023
- 12-bit function: Clamp to 0-4095

## 12-bit RGB Customization Guide

### Understanding the 36-Byte Structure

The 12-bit RGB format packs 8 pixels into 36 bytes. Each pixel contributes 4.5 bytes (36 bits):

```
Pixel 0: 36 bits (4.5 bytes)
Pixel 1: 36 bits (4.5 bytes)
...
Pixel 7: 36 bits (4.5 bytes)
Total:  288 bits (36 bytes)
```

### Channel Bit Distribution

Each 12-bit channel is split as follows:
- **Low 8 bits**: Channel[7:0] - Stored in separate bytes
- **High 4 bits**: Channel[11:8] - Packed into combined bytes

### Customization Steps

1. **Identify the Correct Pattern**: Determine the exact interleaving pattern required by your DeckLink hardware
2. **Modify the Helper Function**: Update `pack_8_pixels_into_36_bytes()` with the correct pattern
3. **Test the Implementation**: Verify the pattern works correctly with your hardware
4. **Optimize if Needed**: Fine-tune the implementation for performance

### Pattern Examples

#### Example 1: Interleaved Low/High Pattern
```cpp
// Interleaves low and high bits across the 36 bytes
for (int i = 0; i < 8; i++) {
    groupPtr[i*3] = r_low[i];     // Every 3rd byte: R_low
    groupPtr[i*3 + 1] = g_low[i]; // Every 3rd byte + 1: G_low  
    groupPtr[i*3 + 2] = b_low[i]; // Every 3rd byte + 2: B_low
}
// High bits packed into remaining bytes...
```

#### Example 2: Planar Pattern
```cpp
// Groups all low bits together, then all high bits
for (int i = 0; i < 8; i++) {
    groupPtr[i] = r_low[i];       // First 8 bytes: R_low
    groupPtr[i + 8] = g_low[i];   // Next 8 bytes: G_low
    groupPtr[i + 16] = b_low[i];  // Next 8 bytes: B_low
}
// High bits packed into remaining 12 bytes...
```

### Testing and Validation

When customizing the 12-bit RGB pattern:

1. **Use Known Test Patterns**: Test with simple patterns (e.g., all red, all green, all blue)
2. **Verify Hardware Compatibility**: Test with actual DeckLink hardware
3. **Check Memory Alignment**: Ensure proper byte alignment
4. **Validate Color Accuracy**: Verify correct color reproduction
5. **Performance Testing**: Measure frame filling performance

## Blackmagic DeckLink API Compatibility

### Hardware Requirements
- All packing schemes are designed to be compatible with Blackmagic DeckLink hardware
- 12-bit RGB interleaved packing follows the exact scheme expected by DeckLink devices
- No color space conversions are performed - hardware expects pre-converted values

### Performance Considerations
- All functions use optimized frame-filling algorithms
- 8-bit and 10-bit formats use efficient 32-bit word packing
- 12-bit RGB uses optimized interleaved packing for hardware processing
- All functions are designed for minimal CPU overhead
- No scaling operations reduce computational cost

### Error Handling
- All functions include bounds checking for memory safety
- Invalid pixel formats fall back to 8-bit BGRA
- Comprehensive logging for debugging
- Automatic range clamping prevents invalid values

## Testing and Validation

### Test Cases
1. **Color Accuracy**: Verify correct color reproduction across all formats
2. **Memory Safety**: Ensure no buffer overruns in all frame-filling functions
3. **Performance**: Measure frame filling performance for each format
4. **Hardware Compatibility**: Test with actual DeckLink devices
5. **Range Validation**: Test edge cases and range clamping
6. **API Consistency**: Verify all functions follow the same frame-filling pattern

### Validation Methods
- Compare output colors with reference implementations
- Use DeckLink hardware monitoring tools
- Verify frame buffer integrity with memory analysis tools
- Test with known color values at different bit depths
- Validate consistent behavior across all pixel formats

## Future Enhancements

### Potential Improvements
1. **SIMD Optimization**: Use vector instructions for faster frame filling
2. **Additional Formats**: Support for more pixel formats as needed
3. **Color Space Options**: Support for different color space matrices
4. **HDR Support**: Enhanced support for HDR color spaces
5. **Optional Scaling**: Add optional scaling functions for convenience

### Extensibility
- Modular design allows easy addition of new pixel formats
- Clear separation of concerns between packing logic and device interface
- Well-documented interfaces for future development
- Range checking can be easily modified or disabled
- Consistent API pattern makes adding new formats straightforward

## References

- Blackmagic DeckLink SDK Documentation
- SMPTE Standards for Digital Video
- BT.709 Color Space Specification
- DeckLink API Reference Manual 