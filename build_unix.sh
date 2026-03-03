#!/bin/bash
# Build script for macOS and Linux

echo "=========================================="
echo "Snapmaker U1 Flasher - Unix Build"
echo "=========================================="

# Detect OS
OS=$(uname -s)
ARCH=$(uname -m)

echo "Detected: $OS $ARCH"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Determine output name and icon flag
if [ "$OS" = "Darwin" ]; then
    OUTPUT_NAME="SnapmakerU1-Flasher-macOS"
    BUNDLE_FLAG="--windowed"
    ICON_FLAG="--icon=icon.ico"
else
    OUTPUT_NAME="SnapmakerU1-Flasher-Linux"
    BUNDLE_FLAG=""
    ICON_FLAG=""
fi

# Build executable
echo "Building executable..."
pyinstaller \
    --onefile \
    $BUNDLE_FLAG \
    $ICON_FLAG \
    --name "$OUTPUT_NAME" \
    --clean \
    snapmaker_u1_flasher.py

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Create app bundle on macOS
if [ "$OS" = "Darwin" ]; then
    echo "Creating macOS app bundle..."
    
    APP_NAME="SnapmakerU1-Flasher.app"
    DIST_DIR="dist/$APP_NAME"
    
    mkdir -p "$DIST_DIR/Contents/MacOS"
    mkdir -p "$DIST_DIR/Contents/Resources"
    
    # Move executable
    mv "dist/$OUTPUT_NAME" "$DIST_DIR/Contents/MacOS/"
    
    # Create Info.plist
    cat > "$DIST_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$OUTPUT_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.paxx12.snapmakeru1flasher</string>
    <key>CFBundleName</key>
    <string>Snapmaker U1 Flasher</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
</dict>
</plist>
EOF

    echo "Created $APP_NAME"
fi

echo ""
echo "=========================================="
echo "Build complete!"
echo "Output: dist/"
echo "=========================================="
