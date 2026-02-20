# Makefile for BMD Signal Generator
# Requires Blackmagic DeckLink SDK

# Compiler and flags
# c++23 (!?!) is required for std::byteswap
CXX = clang++
CXXFLAGS = -std=c++20 -Wall -O2 -fPIC -I"Blackmagic DeckLink SDK 15.3/Mac/include"
LDFLAGS = -dynamiclib -framework CoreFoundation -F/Library/Frameworks -framework DeckLinkAPI

# Source files
SRC = decklink_wrapper.cpp pixel_packing.cpp
TARGET = ../bmd_sg/decklink/libdecklink.dylib

# Default target
all: $(TARGET)

# Link the executable
$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

# Clean build artifacts
clean:
	rm -f $(TARGET)

# Install target (optional)
install: $(TARGET)
	cp $(TARGET) /usr/local/lib/

# Uninstall target
uninstall:
	rm -f /usr/local/lib/$(TARGET)

# Show help
help:
	@echo "Available targets:"
	@echo "  all       - Build the executable (default)"
	@echo "  clean     - Remove build artifacts"
	@echo "  install   - Install to /usr/local/lib/"
	@echo "  uninstall - Remove from /usr/local/lib/"
	@echo "  help      - Show this help message"

# Phony targets
.PHONY: all clean install uninstall help 