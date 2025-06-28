#include "draw_image.h"
#include "pixel_packing.h"
#include <algorithm>
#include <iostream>
#include <vector>

/*
 * Draw Image Implementation for Blackmagic DeckLink API
 * 
 * This file contains the implementation of functions for drawing/filling frame buffers
 * with various types of image data. These functions handle the creation of image data
 * and then use the pixel packing functions to convert it to the required format.
 * 
 * INPUT RANGES:
 * - 8-bit functions: Expect 8-bit values (0-255)
 * - 10-bit functions: Expect 10-bit values (0-1023)
 * - 12-bit function: Expect 12-bit values (0-4095)
 * 
 * All functions include range checking and will clamp values to valid ranges.
 */

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
    
    // Create temporary arrays filled with the solid color
    std::vector<uint8_t> r_data(width * height, r);
    std::vector<uint8_t> g_data(width * height, g);
    std::vector<uint8_t> b_data(width * height, b);
    
    // Use the packing function to fill the frame
    pack_8bit_rgb_image(frameData, r_data.data(), g_data.data(), b_data.data(), 
                       width, height, rowBytes, isBGRA);
    
    std::cerr << "[DrawImage] 8-bit RGB frame filled: " << width << "x" << height 
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
    
    // Clamp values to 10-bit range (0-1023)
    r = std::min(r, static_cast<uint16_t>(1023));
    g = std::min(g, static_cast<uint16_t>(1023));
    b = std::min(b, static_cast<uint16_t>(1023));
    
    // Create temporary arrays filled with the solid color
    std::vector<uint16_t> r_data(width * height, r);
    std::vector<uint16_t> g_data(width * height, g);
    std::vector<uint16_t> b_data(width * height, b);
    
    // Use the packing function to fill the frame
    pack_10bit_rgb_image(frameData, r_data.data(), g_data.data(), b_data.data(), 
                        width, height, rowBytes);
    
    std::cerr << "[DrawImage] 10-bit RGB frame filled: " << width << "x" << height 
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
    
    // Clamp values to 10-bit range (0-1023)
    y = std::min(y, static_cast<uint16_t>(1023));
    u = std::min(u, static_cast<uint16_t>(1023));
    v = std::min(v, static_cast<uint16_t>(1023));
    
    // Create temporary arrays filled with the solid color
    std::vector<uint16_t> y_data(width * height, y);
    std::vector<uint16_t> u_data(width * height, u);
    std::vector<uint16_t> v_data(width * height, v);
    
    // Use the packing function to fill the frame
    pack_10bit_yuv_image(frameData, y_data.data(), u_data.data(), v_data.data(), 
                        width, height, rowBytes);
    
    std::cerr << "[DrawImage] 10-bit YUV frame filled: " << width << "x" << height 
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
    
    // Clamp values to 12-bit range (0-4095)
    r = std::min(r, static_cast<uint16_t>(4095));
    g = std::min(g, static_cast<uint16_t>(4095));
    b = std::min(b, static_cast<uint16_t>(4095));
    
    // Create temporary arrays filled with the solid color
    std::vector<uint16_t> r_data(width * height, r);
    std::vector<uint16_t> g_data(width * height, g);
    std::vector<uint16_t> b_data(width * height, b);
    
    // Use the packing function to fill the frame
    pack_12bit_rgb_image(frameData, r_data.data(), g_data.data(), b_data.data(), 
                        width, height, rowBytes);
    
    std::cerr << "[DrawImage] 12-bit RGB frame filled successfully with interleaved packing" << std::endl;
} 