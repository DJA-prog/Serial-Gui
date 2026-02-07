#!/bin/bash
# Build script for Serial Communication Monitor on Linux
# Usage: ./build_linux.sh [release|debug]
#        Default is 'release' if no parameter provided

BUILD_MODE=${1:-release}
VERSION="2.5.0"

# Validate build mode
if [[ "$BUILD_MODE" != "release" && "$BUILD_MODE" != "debug" ]]; then
    echo "Error: Invalid build mode '$BUILD_MODE'"
    echo "Usage: ./build_linux.sh [release|debug]"
    exit 1
fi

# Add 'd' suffix for debug builds
if [[ "$BUILD_MODE" == "debug" ]]; then
    VERSION_SUFFIX="${VERSION}d"
    BUILD_TYPE="DEBUG"
else
    VERSION_SUFFIX="$VERSION"
    BUILD_TYPE="RELEASE"
fi

echo "=================================================="
echo "Serial Communication Monitor - Linux Build Script"
echo "=================================================="
echo "Build Mode: $BUILD_TYPE"
echo "Version: $VERSION_SUFFIX"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found in PATH"
    exit 1
fi

echo "Found Python: $(python3 --version)"

# Check for PyInstaller
if ! python3 -m PyInstaller --version &> /dev/null; then
    echo "PyInstaller not found, installing..."
    python3 -m pip install pyinstaller
fi

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build dist *.spec
echo "  Removed build artifacts"

# Verify icon exists
if [[ ! -f "images/icon.png" ]]; then
    echo "Error: Icon file not found at images/icon.png"
    exit 1
fi

# Build the executable
echo ""
echo "Building executable with PyInstaller..."
echo ""

# Base command
PYINSTALLER_CMD="python3 -m PyInstaller \
    --onefile \
    --name=Serial_monitor_${VERSION_SUFFIX}_x86-64 \
    --icon=images/icon.png \
    --add-data=images/icon.png:images \
    --add-data=commands:commands \
    --clean \
    --noconfirm"

# Add mode-specific flags
if [[ "$BUILD_MODE" == "debug" ]]; then
    echo "Debug mode enabled: Console output will be visible"
    PYINSTALLER_CMD="$PYINSTALLER_CMD --console --debug=all"
else
    echo "Release mode: GUI-only executable"
    PYINSTALLER_CMD="$PYINSTALLER_CMD --windowed"
fi

# Add entry point
PYINSTALLER_CMD="$PYINSTALLER_CMD App.py"

# Execute build
eval $PYINSTALLER_CMD

if [[ $? -eq 0 ]]; then
    echo ""
    echo "=================================================="
    echo "Build completed successfully! ($BUILD_TYPE)"
    echo "=================================================="
    echo ""
    echo "Executable location: dist/Serial_monitor_${VERSION_SUFFIX}_x86-64"
    echo ""
    
    if [[ -f "dist/Serial_monitor_${VERSION_SUFFIX}_x86-64" ]]; then
        FILE_SIZE=$(du -h "dist/Serial_monitor_${VERSION_SUFFIX}_x86-64" | cut -f1)
        echo "File size: $FILE_SIZE"
        echo ""
        
        # Make executable
        chmod +x "dist/Serial_monitor_${VERSION_SUFFIX}_x86-64"
        echo "Executable permissions set"
        
        if [[ "$BUILD_MODE" == "debug" ]]; then
            echo ""
            echo "Debug build notes:"
            echo "  - Console output will be visible for debugging"
            echo "  - Version suffix includes 'd' ($VERSION_SUFFIX)"
        else
            echo ""
            echo "You can now distribute the executable independently."
            echo "Note: First run may create config directory in ~/.config/SerialCommunicationMonitor"
        fi
    fi
else
    echo ""
    echo "=================================================="
    echo "Build failed! Check the error messages above."
    echo "=================================================="
    exit 1
fi
