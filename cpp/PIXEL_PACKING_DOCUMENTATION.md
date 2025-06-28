# Pixel Packing Implementation Documentation

## Overview

This document describes the pixel packing schemes implemented for Blackmagic DeckLink devices. The implementation has been refactored into separate files for better organization and maintainability.

## File Structure

- `pixel_packing.h` - Header file with function declarations and documentation
- `pixel_packing.cpp` - Implementation of all pixel packing functions
- `decklink_wrapper.cpp` - Main wrapper that uses the pixel packing functions

## Supported Pixel Formats

### 1. 8-bit RGB Formats

#### BGRA Format (`bmdFormat8BitBGRA`)
- **Structure**: 32-bit word with alpha channel
- **Byte Order**: AABBGGRR (Alpha, Blue, Green, Red)
- **Alpha**: Set to 0xFF (fully opaque)
- **Function**: `pack_8bit_rgb(r, g, b, true)`

#### ARGB Format (`bmdFormat8BitARGB`)
- **Structure**: 32-bit word with alpha channel
- **Byte Order**: AARRGGBB (Alpha, Red, Green, Blue)
- **Alpha**: Set to 0xFF (fully opaque)
- **Function**: `pack_8bit_rgb(r, g, b, false)`

### 2. 10-bit RGB Format (`bmdFormat10BitRGB`)

#### Scaling Algorithm
- **Input**: 8-bit RGB values (0-255)
- **Output**: 10-bit RGB values (0-1023)
- **Method**: Bit replication for proper scaling
- **Formula**: `value_10bit = (value_8bit << 2) | (value_8bit >> 6)`

#### Packing Structure
- **Bits 0-9**: Blue channel (10 bits)
- **Bits 10-19**: Green channel (10 bits)
- **Bits 20-29**: Red channel (10 bits)
- **Bits 30-31**: Unused (padding)
- **Function**: `pack_10bit_rgb(r, g, b)`

### 3. 10-bit YUV Format (`bmdFormat10BitYUV`)

#### Color Space Conversion
Uses BT.709 color space conversion matrix:

```
Y = 0.2126*R + 0.7152*G + 0.0722*B
U = -0.1146*R - 0.3854*G + 0.5000*B
V = 0.5000*R - 0.4542*G - 0.0458*B
```

#### Scaling and Packing
- **Y**: 0-1023 (10-bit range)
- **U**: 512-1023 (centered around 512)
- **V**: 512-1023 (centered around 512)
- **Bits 0-9**: U channel (10 bits)
- **Bits 10-19**: Y channel (10 bits)
- **Bits 20-29**: V channel (10 bits)
- **Bits 30-31**: Unused (padding)
- **Function**: `pack_10bit_yuv(r, g, b)`

### 4. 12-bit RGB Format (`bmdFormat12BitRGB`)

#### Complex Interleaved Packing Scheme

This is the most complex format, requiring special handling due to the interleaved packing scheme used by Blackmagic DeckLink devices.

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

##### Color Range Conversion
- **Input**: 8-bit RGB (0-255 per channel)
- **Output**: 12-bit RGB (0-4095 per channel)
- **Scaling**: `value_12bit = (value_8bit * 4095) / 255`
- **Function**: `fill_12bit_rgb_frame(frameData, width, height, rowBytes, r, g, b)`

## Implementation Details

### Function Signatures

```cpp
// 8-bit RGB packing
uint32_t pack_8bit_rgb(uint8_t r, uint8_t g, uint8_t b, bool isBGRA = true);

// 10-bit RGB packing
uint32_t pack_10bit_rgb(uint8_t r, uint8_t g, uint8_t b);

// 10-bit YUV packing
uint32_t pack_10bit_yuv(uint8_t r, uint8_t g, uint8_t b);

// 12-bit RGB frame filling
void fill_12bit_rgb_frame(void* frameData, int32_t width, int32_t height, 
                         int32_t rowBytes, uint8_t r, uint8_t g, uint8_t b);
```

### Usage in Main Wrapper

The main wrapper (`decklink_wrapper.cpp`) uses these functions in the `fillFrameWithColor()` method:

```cpp
switch (m_pixelFormat) {
    case bmdFormat8BitBGRA:
        color = pack_8bit_rgb(m_r, m_g, m_b, true);
        break;
    case bmdFormat8BitARGB:
        color = pack_8bit_rgb(m_r, m_g, m_b, false);
        break;
    case bmdFormat10BitRGB:
        color = pack_10bit_rgb(m_r, m_g, m_b);
        break;
    case bmdFormat10BitYUV:
        color = pack_10bit_yuv(m_r, m_g, m_b);
        break;
    case bmdFormat12BitRGB:
        // Handled separately with fill_12bit_rgb_frame()
        break;
}
```

## Blackmagic DeckLink API Compatibility

### Hardware Requirements
- All packing schemes are designed to be compatible with Blackmagic DeckLink hardware
- 12-bit RGB interleaved packing follows the exact scheme expected by DeckLink devices
- Color space conversions use industry-standard BT.709 matrix

### Performance Considerations
- 8-bit and 10-bit formats use efficient 32-bit word packing
- 12-bit RGB uses optimized interleaved packing for hardware processing
- All functions are designed for minimal CPU overhead

### Error Handling
- All functions include bounds checking for memory safety
- Invalid pixel formats fall back to 8-bit BGRA
- Comprehensive logging for debugging

## Testing and Validation

### Test Cases
1. **Color Accuracy**: Verify correct color reproduction across all formats
2. **Memory Safety**: Ensure no buffer overruns in 12-bit RGB packing
3. **Performance**: Measure frame filling performance for each format
4. **Hardware Compatibility**: Test with actual DeckLink devices

### Validation Methods
- Compare output colors with reference implementations
- Use DeckLink hardware monitoring tools
- Verify frame buffer integrity with memory analysis tools

## Future Enhancements

### Potential Improvements
1. **SIMD Optimization**: Use vector instructions for faster packing
2. **Additional Formats**: Support for more pixel formats as needed
3. **Color Space Options**: Support for different color space matrices
4. **HDR Support**: Enhanced support for HDR color spaces

### Extensibility
- Modular design allows easy addition of new pixel formats
- Clear separation of concerns between packing logic and device interface
- Well-documented interfaces for future development

## References

- Blackmagic DeckLink SDK Documentation
- SMPTE Standards for Digital Video
- BT.709 Color Space Specification
- DeckLink API Reference Manual 