#include "pixel_packing.h"
#include <algorithm>
#include <iostream>
#include <cstring>
#include <vector>

/*
 * Pixel Packing for Blackmagic DeckLink API
 * 
 * This file contains the implementation of various pixel packing schemes
 * used by Blackmagic DeckLink devices. Each function handles the specific
 * bit depth and packing requirements per the DeckLink SDK documentation.
 * 
 * INPUT RANGES:
 * - 8-bit functions: Expect 8-bit values (0-255) in a 16-bit container
 * - 10-bit functions: Expect 10-bit values (0-1023) in a 16-bit container
 * - 12-bit function: Expect 12-bit values (0-4095) in a 16-bit container
 * 
 * All functions include range checking and will clamp values to valid ranges.
 * These functions are focused purely on packing existing image data.
 * Specifically, the YUV packing functions simply pack the data, they do not
 * perform any RGB to YUV conversion
 */



void pack_8bpc_rgb_image(
    void* destData,
    const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
    uint16_t width, uint16_t height,
    uint16_t rowBytes,
    bool isBGRA) {
    /*
     * Pack 8-bit RGB image data into BGRA/ARGB format
     * 
     * Packs existing 8-bit RGB image data into BGRA or ARGB format.
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(destData);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int srcIndex = y * width + x;
            int destIndex = y * (rowBytes / 4) + x;
            
            uint8_t r = srcR[srcIndex];
            uint8_t g = srcG[srcIndex];
            uint8_t b = srcB[srcIndex];
            
            uint32_t color;
            if (isBGRA) {
                // BGRA format: AABBGGRR
                color = (0xFF << 24) | (r << 16) | (g << 8) | b;
            } else {
                // ARGB format: AARRGGBB  
                color = (0xFF << 24) | (b << 16) | (g << 8) | r;
            }
            
            pixels[destIndex] = color;
        }
    }
    
    std::cerr << "[PixelPacking] 8-bit RGB image packed: " << width << "x" << height 
              << " into " << (isBGRA ? "BGRA" : "ARGB") << " format" << std::endl;
}

void pack_10bpc_rgb_image(void* destData, const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
                         uint16_t width, uint16_t height, uint16_t rowBytes) {
    /*
     * Pack 10-bit RGB image data into 10-bit RGB format
     * 
     * Packs existing 10-bit RGB image data into 10-bit RGB format.
     * This function separates the packing logic from frame filling.
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(destData);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int srcIndex = y * width + x;
            int destIndex = y * (rowBytes / 4) + x;
            
            uint16_t r = std::min(srcR[srcIndex], static_cast<uint16_t>(1023));
            uint16_t g = std::min(srcG[srcIndex], static_cast<uint16_t>(1023));
            uint16_t b = std::min(srcB[srcIndex], static_cast<uint16_t>(1023));
            
            // Pack into 32-bit word: B[9:0] | G[9:0] << 10 | R[9:0] << 20
            uint32_t color = (b & 0x3FF) | ((g & 0x3FF) << 10) | ((r & 0x3FF) << 20);
            
            pixels[destIndex] = color;
        }
    }
    
    std::cerr << "[PixelPacking] 10-bit RGB image packed: " << width << "x" << height << std::endl;
}

void pack_10bpc_yuv_image(void* destData, const uint16_t* srcY, const uint16_t* srcU, const uint16_t* srcV,
                         uint16_t width, uint16_t height, uint16_t rowBytes) {
    /*
     * Pack 10-bit YUV image data into 10-bit YUV format
     * 
     * Packs existing 10-bit YUV image data into 10-bit YUV format.
     * This function separates the packing logic from frame filling.
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(destData);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int srcIndex = y * width + x;
            int destIndex = y * (rowBytes / 4) + x;
            
            uint16_t y_val = std::min(srcY[srcIndex], static_cast<uint16_t>(1023));
            uint16_t u = std::min(srcU[srcIndex], static_cast<uint16_t>(1023));
            uint16_t v = std::min(srcV[srcIndex], static_cast<uint16_t>(1023));
            
            // Pack into 32-bit word: U[9:0] | Y[9:0] << 10 | V[9:0] << 20
            uint32_t color = (u & 0x3FF) | ((y_val & 0x3FF) << 10) | ((v & 0x3FF) << 20);
            
            pixels[destIndex] = color;
        }
    }
    
    std::cerr << "[PixelPacking] 10-bit YUV image packed: " << width << "x" << height << std::endl;
}

/**
 * Swizzle a portion of two 12-bit color channels into a single byte
 * 
 * Takes two 12-bit color channels and swizzles a portion of them into a single
 * byte with the following format:
 * low 4 bits of channel B, high 4 bits of channel A
 * 
 * @param channelA First 12-bit channel (0-4095)
 * @param channelB Second 12-bit channel (0-4095)
 * @return Swizzled byte with low 4 bits of A and high 4 bits of B
 */
static uint8_t swizzle_two_12(uint16_t channelA, uint16_t channelB) {
    // Extract 4 bits from each channel
    uint8_t b_high_4bits = (channelB & 0xF0) >> 4;  // channelB[11:8]
    uint8_t a_low_4bits = channelA & 0x0F;  // channelA[3:0]
    
    // Swizzle into single byte: [A_low_4bits][B_high_4bits]
    // This puts A's low 4 bits in the high 4 bits of the output byte
    return (a_low_4bits << 4) | b_high_4bits;
}

/**
 * Extract the high 8 bits from a 12-bit color channel
 * 
 * Takes a 12-bit color channel and extracts the high 8 bits (bits 11-4)
 * 
 * @param channel 12-bit channel (0-4095)
 * @return High 8 bits of the channel (bits 11-4)
 */
static uint8_t high_8_of_12(uint16_t channel) {
    return (channel >> 4) & 0xFF;
}

/**
 * Extract the low 8 bits from a 12-bit color channel
 * 
 * Takes a 12-bit color channel and extracts the low 8 bits (bits 7-0)
 * 
 * @param channel 12-bit channel (0-4095)
 * @return Low 8 bits of the channel (bits 7-0)
 */
static uint8_t low_8_of_12(uint16_t channel) {
    return channel & 0xFF;
}

/**
 * Helper function to pack 8 pixels into 36 bytes
 * bmdFormat12BitRGB : 'R12B'
 * Big-endian RGB 12-bit per component with full range (0-4095).
 * Packed as 12-bit per component.
 * This 12-bit pixel format is compatible with SMPTE 268M Digital
 * Moving-Picture Exchange version 1, Annex C, Method C4 packing.
 * int framesize = ((Width * 36) / 8) * Height
 *               = rowbytes * Height
 * In this format, 8 pixels fit into 36 bytes.
 */
static void pack_8_12bpc_pixels_into_36_bytes(uint8_t* groupPtr, 
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
    
    // word 0
    groupPtr[3] = low_8_of_12(r_channels[0]);
    groupPtr[2] = swizzle_two_12(g_channels[0], r_channels[0]);
    groupPtr[1] = high_8_of_12(g_channels[0]);
    groupPtr[0] = low_8_of_12(b_channels[0]);

    // word 1
    groupPtr[7] = swizzle_two_12(r_channels[1], b_channels[0]);
    groupPtr[6] = high_8_of_12(r_channels[1]);
    groupPtr[5] = low_8_of_12(g_channels[1]);
    groupPtr[4] = swizzle_two_12(b_channels[1], g_channels[1]);

    // word 2
    groupPtr[11] = high_8_of_12(b_channels[1]);
    groupPtr[10] = low_8_of_12(r_channels[2]);
    groupPtr[9] = swizzle_two_12(g_channels[2], r_channels[2]);
    groupPtr[8] = high_8_of_12(g_channels[2]);

    // word 3
    groupPtr[15] = low_8_of_12(b_channels[2]);
    groupPtr[14] = swizzle_two_12(r_channels[3], b_channels[2]);
    groupPtr[13] = high_8_of_12(r_channels[3]);
    groupPtr[12] = low_8_of_12(g_channels[3]);

    // word 4
    groupPtr[19] = swizzle_two_12(b_channels[3], g_channels[3]);
    groupPtr[18] = high_8_of_12(b_channels[3]);
    groupPtr[17] = low_8_of_12(r_channels[4]);
    groupPtr[16] = swizzle_two_12(g_channels[4], r_channels[4]);

    // word 5
    groupPtr[23] = high_8_of_12(g_channels[4]);
    groupPtr[22] = low_8_of_12(b_channels[4]);
    groupPtr[21] = swizzle_two_12(r_channels[5], b_channels[4]);
    groupPtr[20] = high_8_of_12(r_channels[5]);
    
    // word 6
    groupPtr[27] = low_8_of_12(g_channels[5]);
    groupPtr[26] = swizzle_two_12(b_channels[5], g_channels[5]);
    groupPtr[25] = high_8_of_12(b_channels[5]);
    groupPtr[24] = low_8_of_12(r_channels[6]);

    // word 7
    groupPtr[31] = swizzle_two_12(g_channels[6], r_channels[6]);
    groupPtr[30] = high_8_of_12(g_channels[6]);
    groupPtr[29] = low_8_of_12(b_channels[6]);
    groupPtr[28] = swizzle_two_12(r_channels[7], b_channels[6]);

    // word 8
    groupPtr[35] = high_8_of_12(r_channels[7]);
    groupPtr[34] = low_8_of_12(g_channels[7]);
    groupPtr[33] = swizzle_two_12(b_channels[7], g_channels[7]);
    groupPtr[32] = high_8_of_12(b_channels[7]);
}

void pack_12bpc_rgb_image(void* destData, const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
                         uint16_t width, uint16_t height, uint16_t rowBytes) {
    /*
     * Pack 12-bit RGB image data into 12-bit RGB format
     * 
     * Packs existing 12-bit RGB image data into 12-bit RGB format using interleaved packing.
     * This function separates the packing logic from frame filling.
     */
    
    uint8_t* bytes = static_cast<uint8_t*>(destData);
    
    std::cerr << "[PixelPacking] Packing 12-bit RGB image: " << width << "x" << height 
              << ", rowBytes: " << rowBytes << std::endl;
    
    for (int y = 0; y < height; y++) {
        uint8_t* row = bytes + (y * rowBytes);
        
        // Process pixels in groups of 8 (36 bytes per group)
        for (int x = 0; x < width; x += 8) {
            // Base address for this pixel group (36 bytes)
            uint8_t* groupPtr = row + ((x / 8) * 36);
            
            // Prepare arrays for the 8 pixels in this group
            uint16_t r_channels[8], g_channels[8], b_channels[8];
            
            // Fill the arrays with image data
            for (int i = 0; i < 8; i++) {
                int pixelX = x + i;
                if (pixelX < width) {
                    int srcIndex = y * width + pixelX;
                    r_channels[i] = std::min(srcR[srcIndex], static_cast<uint16_t>(4095));
                    g_channels[i] = std::min(srcG[srcIndex], static_cast<uint16_t>(4095));
                    b_channels[i] = std::min(srcB[srcIndex], static_cast<uint16_t>(4095));
                } else {
                    // Pad with zeros if we're at the end of a row
                    r_channels[i] = 0;
                    g_channels[i] = 0;
                    b_channels[i] = 0;
                }
            }
            
            // Use the helper function to pack 8 pixels into 36 bytes
            pack_8_12bpc_pixels_into_36_bytes(groupPtr, r_channels, g_channels, b_channels);
        }
    }
    
    std::cerr << "[PixelPacking] 12-bit RGB image packed successfully with interleaved packing" << std::endl;
} 