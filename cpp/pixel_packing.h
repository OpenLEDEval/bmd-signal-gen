#ifndef PIXEL_PACKING_H
#define PIXEL_PACKING_H

#include <cstdint>

#include "DeckLinkAPI.h"

/*
 * Pixel Packing Schemes for Blackmagic DeckLink API
 *
 * This header defines the interface for packing image data into various pixel
 * formats supported by Blackmagic DeckLink devices. Each function handles the
 * specific bit depth and packing requirements per the DeckLink SDK
 * documentation section 3.4.
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

int pack_pixel_format(void* destData,
                      BMDPixelFormat pixelFormat,
                      const uint16_t* srcData,
                      uint16_t width,
                      uint16_t height,
                      uint16_t rowBytes);

#endif  // PIXEL_PACKING_H