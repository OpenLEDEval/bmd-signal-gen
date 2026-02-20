cmake_minimum_required(VERSION 3.20)

# Project configuration
project(bmd_signal_generator
    VERSION 0.1.0
    DESCRIPTION "BMD Signal Generator C++ Library"
    LANGUAGES CXX
)

# Generate compile_commands.json for clang-tidy
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# C++ standard (note: comment in Makefile mentions c++23 for std::byteswap, but uses c++20)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Platform-specific configuration
if(APPLE)
    # macOS-specific settings
    set(DECKLINK_SDK_PATH "Blackmagic DeckLink SDK 15.3/Mac/include")
    set(OUTPUT_NAME "libdecklink.dylib")
    set(DECKLINK_FRAMEWORKS 
        CoreFoundation
        DeckLinkAPI
    )
    set(FRAMEWORK_SEARCH_PATH "/Library/Frameworks")
elseif(WIN32)
    # Windows-specific settings
    set(DECKLINK_SDK_PATH "Blackmagic DeckLink SDK 15.3/Win/include")
    set(OUTPUT_NAME "decklink.dll")
    # Windows will need different linking setup
elseif(UNIX)
    # Linux-specific settings
    set(DECKLINK_SDK_PATH "Blackmagic DeckLink SDK 15.3/Linux/include")
    set(OUTPUT_NAME "libdecklink.so")
    # Linux will need different linking setup
endif()

# Source files
set(SOURCES
    decklink_wrapper.cpp
    pixel_packing.cpp
)

# Create shared library
add_library(decklink_lib SHARED ${SOURCES})

# Set output properties
set_target_properties(decklink_lib PROPERTIES
    OUTPUT_NAME "decklink"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../bmd_sg/decklink"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../bmd_sg/decklink"  # For Windows DLLs
)

# Include directories
target_include_directories(decklink_lib PRIVATE
    "${DECKLINK_SDK_PATH}"
)

# Compiler flags
target_compile_options(decklink_lib PRIVATE
    -Wall
    -O2
    $<$<PLATFORM_ID:Darwin,Linux>:-fPIC>
)

# Platform-specific linking
if(APPLE)
    # Add framework search path
    target_link_options(decklink_lib PRIVATE -F${FRAMEWORK_SEARCH_PATH})
    # Link with frameworks
    foreach(framework ${DECKLINK_FRAMEWORKS})
        target_link_libraries(decklink_lib PRIVATE "-framework ${framework}")
    endforeach()
elseif(WIN32)
    # Windows-specific linking will go here
    # target_link_libraries(decklink_lib PRIVATE ...)
elseif(UNIX)
    # Linux-specific linking will go here
    # target_link_libraries(decklink_lib PRIVATE ...)
endif()

# Custom targets for compatibility with existing workflow
add_custom_target(show_help
    COMMAND ${CMAKE_COMMAND} -E echo "Available targets:"
    COMMAND ${CMAKE_COMMAND} -E echo "  decklink_lib  - Build the shared library (default)"
    COMMAND ${CMAKE_COMMAND} -E echo "  clean         - Remove build artifacts"
    COMMAND ${CMAKE_COMMAND} -E echo "  install       - Install to system location"
    COMMAND ${CMAKE_COMMAND} -E echo "  show_help     - Show this help message"
    COMMENT "Showing available targets"
)

# Install configuration (optional)
install(TARGETS decklink_lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)