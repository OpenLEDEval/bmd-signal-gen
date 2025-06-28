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

### 4. 12-bit RGB Format (`bmdFormat12BitRGB`)

#### Complex Interleaved Packing Scheme

This is the most complex format, requiring special handling due to the interleaved packing scheme used by Blackmagic DeckLink devices.

##### Direct 12-bit Input (No Scaling)
- **Input**: 12-bit RGB values (0-4095) - NO SCALING PERFORMED
- **Output**: Interleaved 12-bit RGB data filling entire frame
- **Method**: Direct packing without scaling

##### Channel Splitting
Each 12-bit RGB channel is split into two parts:
- **Low 8 bits**: Channel[7:0] (stored in separate bytes)
- **High 4 bits**: Channel[11:8] (packed into combined bytes)

##### Memory Layout
- **Per Pixel**: 36 bits (4.5 bytes)
- **Per Group**: 8 pixels fit into 36 bytes (288 bits total)
- **Row Alignment**: Follows DeckLink API requirements

##### Byte Structure (per pixel)
```
Byte 0: R_low[7:0]                    (Red low 8 bits)
Byte 1: G_low[7:0]                    (Green low 8 bits)
Byte 2: B_low[7:0]                    (Blue low 8 bits)
Byte 3: R_high[3:0] | G_high[3:0]<<4  (Red high 4 bits + Green high 4 bits)
Byte 4: B_high[3:0] | (unused bits)   (Blue high 4 bits + padding)
```

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

// 12-bit RGB frame filling (expects 12-bit values)
void fill_12bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes, 
                         uint16_t r, uint16_t g, uint16_t b);
```

### Range Checking
All functions include automatic range checking and will clamp values to the valid range for their respective bit depth:
- 8-bit functions: Clamp to 0-255
- 10-bit functions: Clamp to 0-1023
- 12-bit function: Clamp to 0-4095


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