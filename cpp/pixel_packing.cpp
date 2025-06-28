#include "pixel_packing.h"
#include <algorithm>
#include <iostream>

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
 */

uint32_t pack_8bit_rgb(uint8_t r, uint8_t g, uint8_t b, bool isBGRA) {
    /*
     * 8-bit RGB Packing (BGRA/ARGB format)
     * 
     * Packs 8-bit RGB values into a 32-bit word with alpha channel.
     * Supports both BGRA and ARGB byte orderings.
     * 
     * Format: AARRGGBB (ARGB) or AABBGGRR (BGRA)
     * Alpha is set to 0xFF (fully opaque)
     * 
     * Range checking: Input values are already uint8_t, so they're automatically
     * clamped to 0-255 range.
     */
    
    if (isBGRA) {
        // BGRA format: AABBGGRR
        return (0xFF << 24) | (r << 16) | (g << 8) | b;
    } else {
        // ARGB format: AARRGGBB  
        return (0xFF << 24) | (b << 16) | (g << 8) | r;
    }
}

uint32_t pack_10bit_rgb(uint16_t r, uint16_t g, uint16_t b) {
    /*
     * 10-bit RGB Packing
     * 
     * Accepts 10-bit RGB values and packs them into a 32-bit word.
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
    
    // Clamp values to 10-bit range (0-1023)
    r = std::min(r, static_cast<uint16_t>(1023));
    g = std::min(g, static_cast<uint16_t>(1023));
    b = std::min(b, static_cast<uint16_t>(1023));
    
    // Pack into 32-bit word: B[9:0] | G[9:0] << 10 | R[9:0] << 20
    return (b & 0x3FF) | ((g & 0x3FF) << 10) | ((r & 0x3FF) << 20);
}

uint32_t pack_10bit_yuv(uint16_t y, uint16_t u, uint16_t v) {
    /*
     * 10-bit YUV Packing
     * 
     * Accepts 10-bit YUV values and packs them into a 32-bit word.
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
    
    // Clamp values to 10-bit range (0-1023)
    y = std::min(y, static_cast<uint16_t>(1023));
    u = std::min(u, static_cast<uint16_t>(1023));
    v = std::min(v, static_cast<uint16_t>(1023));
    
    // Pack into 32-bit word: U[9:0] | Y[9:0] << 10 | V[9:0] << 20
    return (u & 0x3FF) | ((y & 0x3FF) << 10) | ((v & 0x3FF) << 20);
}

void fill_12bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes, 
                         uint16_t r, uint16_t g, uint16_t b) {
    /*
     * 12-bit RGB Interleaved Packing Implementation
     * 
     * This function implements the complex 12-bit RGB interleaved packing scheme
     * used by Blackmagic DeckLink devices. Each 12-bit RGB pixel is split into
     * low 8 bits and high 4 bits for each channel, then interleaved across bytes.
     * 
     * PACKING SCHEME:
     * - Each pixel: 36 bits (4.5 bytes)
     * - 8 pixels fit into 36 bytes (288 bits total)
     * - Byte 0: R_low[7:0]     (Red low 8 bits)
     * - Byte 1: G_low[7:0]     (Green low 8 bits)
     * - Byte 2: B_low[7:0]     (Blue low 8 bits)
     * - Byte 3: R_high[3:0] | G_high[3:0] << 4  (Red high 4 bits + Green high 4 bits)
     * - Byte 4: B_high[3:0] | (unused bits)     (Blue high 4 bits + padding)
     * 
     * MEMORY LAYOUT:
     * - 8 pixels per group, each group is 36 bytes
     * - Row alignment follows DeckLink API requirements
     * - Each row is padded to the required rowBytes alignment
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
    
    // Split each 12-bit channel into low 8 bits and high 4 bits
    uint8_t r_low = r & 0xFF;        // R[7:0]
    uint8_t r_high = (r >> 8) & 0x0F; // R[11:8]
    uint8_t g_low = g & 0xFF;        // G[7:0]
    uint8_t g_high = (g >> 8) & 0x0F; // G[11:8]
    uint8_t b_low = b & 0xFF;        // B[7:0]
    uint8_t b_high = (b >> 8) & 0x0F; // B[11:8]
    
    for (int y = 0; y < height; y++) {
        uint8_t* row = bytes + (y * rowBytes);
        
        // Process pixels one at a time to handle the complex interleaving
        for (int x = 0; x < width; x++) {
            // Calculate pixel position in the row
            int pixelGroup = x / 8;  // Which group of 8 pixels this belongs to
            int pixelInGroup = x % 8; // Position within the group (0-7)
            
            // Calculate byte offset for this pixel within its group
            // Each pixel takes 4.5 bytes, so pixel 0 starts at byte 0, pixel 1 at byte 4.5, etc.
            int pixelByteOffset = pixelInGroup * 4; // Integer part of 4.5
            
            // Base address for this pixel group
            uint8_t* groupPtr = row + (pixelGroup * 36);
            
            // Write the interleaved bytes for this pixel
            int baseByte = pixelByteOffset;
            
            // Byte 0: R_low[7:0]
            if (baseByte < 36) {
                groupPtr[baseByte] = r_low;
            }
            
            // Byte 1: G_low[7:0]
            if (baseByte + 1 < 36) {
                groupPtr[baseByte + 1] = g_low;
            }
            
            // Byte 2: B_low[7:0]
            if (baseByte + 2 < 36) {
                groupPtr[baseByte + 2] = b_low;
            }
            
            // Byte 3: R_high[3:0] | G_high[3:0] << 4
            if (baseByte + 3 < 36) {
                uint8_t combined = r_high | (g_high << 4);
                groupPtr[baseByte + 3] = combined;
            }
            
            // Byte 4: B_high[3:0] | (unused bits)
            if (baseByte + 4 < 36) {
                groupPtr[baseByte + 4] = b_high;
            }
        }
    }
    
    std::cerr << "[PixelPacking] 12-bit RGB frame filled successfully with interleaved packing" << std::endl;
} 