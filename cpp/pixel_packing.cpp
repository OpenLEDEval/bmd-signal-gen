#include "pixel_packing.h"
#include <algorithm>
#include <iostream>
#include <cstring>

/*
 * Pixel Packing Implementation for Blackmagic DeckLink API
 * 
 * This file contains the implementation of various pixel packing schemes
 * used by Blackmagic DeckLink devices. Each function handles the specific
 * bit depth and packing requirements for optimal hardware compatibility.
 * 
 * INPUT RANGES:
 * - 8-bit functions: Expect 8-bit values (0-255)
 * - 10-bit functions: Expect 10-bit values (0-1023)
 * - 12-bit function: Expect 12-bit values (0-4095)
 * 
 * All functions include range checking and will clamp values to valid ranges.
 * All functions fill entire frames with the specified color.
 */

/**
 * Swizzle a portion of two 12-bit color channels into a single byte
 * 
 * Takes two 12-bit color channels and swizzles a portion of them into a single byte with
 * the following format: low 4 bits of channel B, high 4 bits of channel A
 * 
 * @param channelA First 12-bit channel (0-4095)
 * @param channelB Second 12-bit channel (0-4095)
 * @return Swizzled byte with low 4 bits of A and high 4 bits of B
 */
static uint8_t pack_two_12bit_channels(uint16_t channelA, uint16_t channelB) {
    /*
     * Pack two 12-bit channels into a single byte
     * 
     * INPUT:
     * - channelA: 12-bit value (0-4095) - low 4 bits will be used
     * - channelB: 12-bit value (0-4095) - high 4 bits will be used
     * 
     * OUTPUT:
     * - Single byte with format: [A_low_4bits][B_high_4bits]
     * 
     * BIT LAYOUT:
     * - Bits 0-3: channelB[11:8] (high 4 bits of channel B, which become low 4 bits in output)
     * - Bits 4-7: channelA[3:0] (low 4 bits of channel A, which become high 4 bits in output)
     */
    
    // Extract 4 bits from each channel
    uint8_t b_high_4bits = (channelB & 0xF0) >> 4;  // channelB[11:8]
    uint8_t a_low_4bits = channelA & 0x0F;  // channelA[3:0]
    
    // Swizzle into single byte: [A_low_4bits][B_high_4bits]
    // This puts A's low 4 bits in the high 4 bits of the output byte
    uint8_t packed_byte = (a_low_4bits << 4) | b_high_4bits;
    
    return packed_byte;
}

/**
 * Extract the high 8 bits from a 12-bit color channel
 * 
 * Takes a 12-bit color channel and extracts the high 8 bits (bits 11-4)
 * 
 * @param channel 12-bit channel (0-4095)
 * @return High 8 bits of the channel (bits 11-4)
 */
static uint8_t high_8bits(uint16_t channel) {
    /*
     * Extract high 8 bits from a 12-bit channel
     * 
     * INPUT:
     * - channel: 12-bit value (0-4095)
     * 
     * OUTPUT:
     * - 8-bit value containing bits 11-4 of the input channel
     * 
     * BIT LAYOUT:
     * - Input:  [11][10][9][8][7][6][5][4][3][2][1][0]
     * - Output: [7][6][5][4][3][2][1][0] (bits 11-4 of input)
     */
    
    // Extract high 8 bits: shift right by 4 to get bits 11-4
    uint8_t high_8bits = (channel >> 4) & 0xFF;
    
    return high_8bits;
}

/**
 * Extract the low 8 bits from a 12-bit color channel
 * 
 * Takes a 12-bit color channel and extracts the low 8 bits (bits 7-0)
 * 
 * @param channel 12-bit channel (0-4095)
 * @return Low 8 bits of the channel (bits 7-0)
 */
static uint8_t low_8bits(uint16_t channel) {
    /*
     * Extract low 8 bits from a 12-bit channel
     * 
     * INPUT:
     * - channel: 12-bit value (0-4095)
     * 
     * OUTPUT:
     * - 8-bit value containing bits 7-0 of the input channel
     * 
     * BIT LAYOUT:
     * - Input:  [11][10][9][8][7][6][5][4][3][2][1][0]
     * - Output: [7][6][5][4][3][2][1][0] (bits 7-0 of input)
     */
    
    // Extract low 8 bits: mask with 0xFF to get bits 7-0
    uint8_t low_8bits = channel & 0xFF;
    
    return low_8bits;
}

/**
 * Helper function to pack 8 pixels into 36 bytes
 * bmdFormat12BitRGB : ‘R12B’
 * Big-endian RGB 12-bit per component with full range (0-4095).
 * Packed as 12-bit per component.
 * This 12-bit pixel format is compatible with SMPTE 268M Digital
 * Moving-Picture Exchange version 1, Annex C, Method C4 packing.
 * int framesize = ((Width * 36) / 8) * Height
 *               = rowbytes * Height
 * In this format, 8 pixels fit into 36 bytes.
 */
static void pack_8_pixels_into_36_bytes(uint8_t* groupPtr, 
                                       const uint16_t r_channels[8], 
                                       const uint16_t g_channels[8], 
                                       const uint16_t b_channels[8]) {
    /**
     * INPUT:
     * - groupPtr: Pointer to 36-byte destination buffer
     * - r_channels[8]: Array of 8 red channel values (12-bit each, 0-4095)
     * - g_channels[8]: Array of 8 green channel values (12-bit each, 0-4095)
     * - b_channels[8]: Array of 8 blue channel values (12-bit each, 0-4095)
     */
    
    // Clear the 36-byte buffer first
    std::memset(groupPtr, 0, 36);
    
    // TODO: Replace this placeholder pattern with the correct interleaving
    // The pattern below is just an example and needs to be customized
    
    // word 0
    groupPtr[3] = low_8bits(r_channels[0]);
    groupPtr[2] = pack_two_12bit_channels(g_channels[0], r_channels[0]);
    groupPtr[1] = high_8bits(g_channels[0]);
    groupPtr[0] = low_8bits(b_channels[0]);

    // word 1
    groupPtr[7] = pack_two_12bit_channels(r_channels[1], b_channels[0]);
    groupPtr[6] = high_8bits(r_channels[1]);
    groupPtr[5] = low_8bits(g_channels[1]);
    groupPtr[4] = pack_two_12bit_channels(b_channels[1], g_channels[1]);

    // word 2
    groupPtr[11] = high_8bits(b_channels[1]);
    groupPtr[10] = low_8bits(r_channels[2]);
    groupPtr[9] = pack_two_12bit_channels(g_channels[2], r_channels[2]);
    groupPtr[8] = high_8bits(g_channels[2]);

    // word 3
    groupPtr[15] = low_8bits(b_channels[2]);
    groupPtr[14] = pack_two_12bit_channels(r_channels[3], b_channels[2]);
    groupPtr[13] = high_8bits(r_channels[3]);
    groupPtr[12] = low_8bits(g_channels[3]);

    // word 4
    groupPtr[19] = pack_two_12bit_channels(b_channels[3], g_channels[3]);
    groupPtr[18] = high_8bits(b_channels[3]);
    groupPtr[17] = low_8bits(r_channels[4]);
    groupPtr[16] = pack_two_12bit_channels(g_channels[4], r_channels[4]);

    // word 5
    groupPtr[23] = high_8bits(g_channels[4]);
    groupPtr[22] = low_8bits(b_channels[4]);
    groupPtr[21] = pack_two_12bit_channels(r_channels[5], b_channels[4]);
    groupPtr[20] = high_8bits(r_channels[5]);
    
    // word 6
    groupPtr[27] = low_8bits(g_channels[5]);
    groupPtr[26] = pack_two_12bit_channels(b_channels[5], g_channels[5]);
    groupPtr[25] = high_8bits(b_channels[5]);
    groupPtr[24] = low_8bits(r_channels[6]);

    // word 7
    groupPtr[31] = pack_two_12bit_channels(g_channels[6], r_channels[6]);
    groupPtr[30] = high_8bits(g_channels[6]);
    groupPtr[29] = low_8bits(b_channels[6]);
    groupPtr[28] = pack_two_12bit_channels(r_channels[7], b_channels[6]);

    // word 8
    groupPtr[35] = high_8bits(r_channels[7]);
    groupPtr[34] = low_8bits(g_channels[7]);
    groupPtr[33] = pack_two_12bit_channels(b_channels[7], g_channels[7]);
    groupPtr[32] = high_8bits(b_channels[7]);
}

void fill_8bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes,
                        uint8_t r, uint8_t g, uint8_t b, bool isBGRA) {
    /*
     * 8-bit RGB Frame Filling (BGRA/ARGB format)
     * 
     * Fills the entire frame with 8-bit RGB values packed into 32-bit words.
     * Supports both BGRA and ARGB byte orderings.
     * 
     * Format: AARRGGBB (ARGB) or AABBGGRR (BGRA)
     * Alpha is set to 0xFF (fully opaque)
     * 
     * Range checking: Input values are already uint8_t, so they're automatically
     * clamped to 0-255 range.
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(frameData);
    uint32_t color;
    
    if (isBGRA) {
        // BGRA format: AABBGGRR
        color = (0xFF << 24) | (r << 16) | (g << 8) | b;
    } else {
        // ARGB format: AARRGGBB  
        color = (0xFF << 24) | (b << 16) | (g << 8) | r;
    }
    
    // Fill the entire frame with the packed color
    for (int i = 0; i < width * height; ++i) {
        pixels[i] = color;
    }
    
    std::cerr << "[PixelPacking] 8-bit RGB frame filled: " << width << "x" << height 
              << " with color (" << (int)r << "," << (int)g << "," << (int)b << ")" << std::endl;
}

void fill_10bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes,
                         uint16_t r, uint16_t g, uint16_t b) {
    /*
     * 10-bit RGB Frame Filling
     * 
     * Fills the entire frame with 10-bit RGB values packed into 32-bit words.
     * No scaling is performed - values should already be in 10-bit range.
     * 
     * PACKING:
     * - Bits 0-9: Blue channel (10 bits)
     * - Bits 10-19: Green channel (10 bits)  
     * - Bits 20-29: Red channel (10 bits)
     * - Bits 30-31: Unused (padding)
     * 
     * RANGE CHECKING:
     * - Clamps values to 0-1023 range (10-bit)
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(frameData);
    
    // Clamp values to 10-bit range (0-1023)
    r = std::min(r, static_cast<uint16_t>(1023));
    g = std::min(g, static_cast<uint16_t>(1023));
    b = std::min(b, static_cast<uint16_t>(1023));
    
    // Pack into 32-bit word: B[9:0] | G[9:0] << 10 | R[9:0] << 20
    uint32_t color = (b & 0x3FF) | ((g & 0x3FF) << 10) | ((r & 0x3FF) << 20);
    
    // Fill the entire frame with the packed color
    for (int i = 0; i < width * height; ++i) {
        pixels[i] = color;
    }
    
    std::cerr << "[PixelPacking] 10-bit RGB frame filled: " << width << "x" << height 
              << " with color (" << r << "," << g << "," << b << ")" << std::endl;
}

void fill_10bit_yuv_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes,
                         uint16_t y, uint16_t u, uint16_t v) {
    /*
     * 10-bit YUV Frame Filling
     * 
     * Fills the entire frame with 10-bit YUV values packed into 32-bit words.
     * No color space conversion is performed - values should already be in YUV space.
     * 
     * PACKING:
     * - Bits 0-9: U channel (10 bits)
     * - Bits 10-19: Y channel (10 bits)
     * - Bits 20-29: V channel (10 bits)
     * - Bits 30-31: Unused (padding)
     * 
     * RANGE CHECKING:
     * - Clamps values to 0-1023 range (10-bit)
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(frameData);
    
    // Clamp values to 10-bit range (0-1023)
    y = std::min(y, static_cast<uint16_t>(1023));
    u = std::min(u, static_cast<uint16_t>(1023));
    v = std::min(v, static_cast<uint16_t>(1023));
    
    // Pack into 32-bit word: U[9:0] | Y[9:0] << 10 | V[9:0] << 20
    uint32_t color = (u & 0x3FF) | ((y & 0x3FF) << 10) | ((v & 0x3FF) << 20);
    
    // Fill the entire frame with the packed color
    for (int i = 0; i < width * height; ++i) {
        pixels[i] = color;
    }
    
    std::cerr << "[PixelPacking] 10-bit YUV frame filled: " << width << "x" << height 
              << " with color (" << y << "," << u << "," << v << ")" << std::endl;
}

void fill_12bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes, 
                         uint16_t r, uint16_t g, uint16_t b) {
    /*
     * 12-bit RGB Interleaved Packing Implementation (Refactored)
     * 
     * This function implements the complex 12-bit RGB interleaved packing scheme
     * used by Blackmagic DeckLink devices. The implementation has been refactored
     * to process 8 separately defined pixels across 36 bytes for easier customization.
     * 
     * PACKING SCHEME:
     * - Each pixel: 36 bits (4.5 bytes)
     * - 8 pixels fit into 36 bytes (288 bits total)
     * - Each 12-bit channel is split into low 8 bits and high 4 bits
     * - The 36 bytes are organized to accommodate 8 pixels with interleaved packing
     * 
     * IMPLEMENTATION:
     * Uses the pack_8_pixels_into_36_bytes helper function to provide a clear
     * structure for defining the correct pixel interleaving pattern.
     * 
     * RANGE CHECKING:
     * - Clamps values to 0-4095 range (12-bit)
     */
    
    uint8_t* bytes = static_cast<uint8_t*>(frameData);
    
    std::cerr << "[PixelPacking] Filling 12-bit RGB frame with interleaved packing: " 
              << width << "x" << height << ", rowBytes: " << rowBytes << std::endl;
    
    // Clamp values to 12-bit range (0-4095)
    r = std::min(r, static_cast<uint16_t>(4095));
    g = std::min(g, static_cast<uint16_t>(4095));
    b = std::min(b, static_cast<uint16_t>(4095));
    
    for (int y = 0; y < height; y++) {
        uint8_t* row = bytes + (y * rowBytes);
        
        // Process pixels in groups of 8 (36 bytes per group)
        for (int x = 0; x < width; x += 8) {
            // Calculate the number of pixels to process in this group
            //int pixelsInThisGroup = std::min(8, width - x);
            
            // Base address for this pixel group (36 bytes)
            uint8_t* groupPtr = row + ((x / 8) * 36);
            
            // Prepare arrays for the 8 pixels in this group
            // For now, all pixels will have the same color (can be customized later)
            uint16_t r_channels[8], g_channels[8], b_channels[8];
            
            // Fill the arrays with the current color values
            for (int i = 0; i < 8; i++) {
                r_channels[i] = r;  // Use full 12-bit red value
                g_channels[i] = g;  // Use full 12-bit green value
                b_channels[i] = b;  // Use full 12-bit blue value
            }
            
            // Use the helper function to pack 8 pixels into 36 bytes
            pack_8_pixels_into_36_bytes(groupPtr, 
                                       r_channels, g_channels, b_channels);
        }
    }
    
    std::cerr << "[PixelPacking] 12-bit RGB frame filled successfully with interleaved packing" << std::endl;
    std::cerr << "[PixelPacking] NOTE: Current implementation uses placeholder interleaving pattern" << std::endl;
    std::cerr << "[PixelPacking] TODO: Replace with correct 8-pixel interleaving across 36 bytes" << std::endl;
} 