#ifndef PIXEL_PACKING_H
#define PIXEL_PACKING_H

#include <cstdint>

/*
 * Pixel Packing Schemes for Blackmagic DeckLink API
 * 
 * This header defines the interface for packing RGB color data into various
 * pixel formats supported by Blackmagic DeckLink devices. Each function
 * handles the specific bit depth and packing requirements for optimal
 * hardware compatibility.
 * 
 * INPUT RANGES:
 * - 8-bit functions: Expect 8-bit values (0-255)
 * - 10-bit functions: Expect 10-bit values (0-1023)
 * - 12-bit function: Expect 12-bit values (0-4095)
 * 
 * All functions include range checking and will clamp values to valid ranges.
 */

/**
 * Pack 8-bit RGB values into 8-bit BGRA/ARGB format
 * 
 * @param r Red channel (0-255, will be clamped if out of range)
 * @param g Green channel (0-255, will be clamped if out of range)
 * @param b Blue channel (0-255, will be clamped if out of range)
 * @param isBGRA true for BGRA format, false for ARGB format
 * @return 32-bit packed pixel value
 */
uint32_t pack_8bit_rgb(uint8_t r, uint8_t g, uint8_t b, bool isBGRA = true);

/**
 * Pack 10-bit RGB values into 10-bit RGB format
 * 
 * Accepts 10-bit RGB values and packs them into a 32-bit word.
 * No scaling is performed - values should already be in 10-bit range.
 * 
 * @param r Red channel (0-1023, will be clamped if out of range)
 * @param g Green channel (0-1023, will be clamped if out of range)
 * @param b Blue channel (0-1023, will be clamped if out of range)
 * @return 32-bit packed pixel value with 10-bit RGB channels
 */
uint32_t pack_10bit_rgb(uint16_t r, uint16_t g, uint16_t b);

/**
 * Pack 10-bit YUV values into 10-bit YUV format
 * 
 * Accepts 10-bit YUV values and packs them into a 32-bit word.
 * No color space conversion is performed - values should already be in YUV space.
 * 
 * @param y Y channel (0-1023, will be clamped if out of range)
 * @param u U channel (0-1023, will be clamped if out of range)
 * @param v V channel (0-1023, will be clamped if out of range)
 * @return 32-bit packed pixel value with 10-bit YUV channels
 */
uint32_t pack_10bit_yuv(uint16_t y, uint16_t u, uint16_t v);

/**
 * Fill a frame buffer with 12-bit RGB data using interleaved packing
 * 
 * This function implements the complex 12-bit RGB interleaved packing scheme
 * used by Blackmagic DeckLink devices. Each 12-bit RGB pixel is split into
 * low 8 bits and high 4 bits for each channel, then interleaved across bytes.
 * 
 * PACKING SCHEME:
 * - Each pixel: 36 bits (4.5 bytes)
 * - 8 pixels fit into 36 bytes
 * - Byte 0: R_low[7:0]
 * - Byte 1: G_low[7:0] 
 * - Byte 2: B_low[7:0]
 * - Byte 3: R_high[3:0] | G_high[3:0] << 4
 * - Byte 4: B_high[3:0] | (unused bits)
 * 
 * @param frameData Pointer to frame buffer
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 * @param r Red channel (0-4095, will be clamped if out of range)
 * @param g Green channel (0-4095, will be clamped if out of range)
 * @param b Blue channel (0-4095, will be clamped if out of range)
 */
void fill_12bit_rgb_frame(void* frameData, int32_t width, int32_t height, int32_t rowBytes, 
                         uint16_t r, uint16_t g, uint16_t b);

#endif // PIXEL_PACKING_H 