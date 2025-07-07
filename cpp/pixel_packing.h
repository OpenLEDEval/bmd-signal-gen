#ifndef PIXEL_PACKING_H
#define PIXEL_PACKING_H

#include <cstdint>

/*
 * Pixel Packing Schemes for Blackmagic DeckLink API
 * 
 * This header defines the interface for packing image data into various pixel formats
 * supported by Blackmagic DeckLink devices. Each function handles the specific bit depth
 * and packing requirements for optimal hardware compatibility.
 * 
 * INPUT RANGES:
 * - 8-bit functions: Expect 8-bit values (0-255)
 * - 10-bit functions: Expect 10-bit values (0-1023)
 * - 12-bit function: Expect 12-bit values (0-4095)
 * 
 * All functions include range checking and will clamp values to valid ranges.
 * These functions are focused purely on packing existing image data.
 */

/**
 * Pack 8-bit RGB image data into BGRA/ARGB format
 * 
 * Packs existing 8-bit RGB image data into BGRA or ARGB format.
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcR Pointer to source red channel data (8-bit, 0-255)
 * @param srcG Pointer to source green channel data (8-bit, 0-255)
 * @param srcB Pointer to source blue channel data (8-bit, 0-255)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 * @param isBGRA true for BGRA format, false for ARGB format
 */
void pack_8bpc_rgb_image(void* destData, const uint8_t* srcR, const uint8_t* srcG, const uint8_t* srcB,
                        int32_t width, int32_t height, int32_t rowBytes, bool isBGRA = true);

/**
 * Pack 10-bit RGB image data into 10-bit RGB format
 * 
 * Packs existing 10-bit RGB image data into 10-bit RGB format.
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcR Pointer to source red channel data (10-bit, 0-1023)
 * @param srcG Pointer to source green channel data (10-bit, 0-1023)
 * @param srcB Pointer to source blue channel data (10-bit, 0-1023)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 */
void pack_10bpc_rgb_image(void* destData, const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
                         int32_t width, int32_t height, int32_t rowBytes);

/**
 * Pack 10-bit YUV image data into 10-bit YUV format
 * 
 * Packs existing 10-bit YUV image data into 10-bit YUV format.
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcY Pointer to source Y channel data (10-bit, 0-1023)
 * @param srcU Pointer to source U channel data (10-bit, 0-1023)
 * @param srcV Pointer to source V channel data (10-bit, 0-1023)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 */
void pack_10bpc_yuv_image(void* destData, const uint16_t* srcY, const uint16_t* srcU, const uint16_t* srcV,
                         int32_t width, int32_t height, int32_t rowBytes);

/**
 * Pack 12-bit RGB image data into 12-bit RGB format
 * 
 * Packs existing 12-bit RGB image data into 12-bit RGB format using interleaved packing.
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcR Pointer to source red channel data (12-bit, 0-4095)
 * @param srcG Pointer to source green channel data (12-bit, 0-4095)
 * @param srcB Pointer to source blue channel data (12-bit, 0-4095)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 */
void pack_12bpc_rgb_image(void* destData, const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
                         int32_t width, int32_t height, int32_t rowBytes);

#endif // PIXEL_PACKING_H 