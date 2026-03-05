# Snapmaker U1 Extended Firmware Flasher

[![Version](https://img.shields.io/badge/version-2.2.3-blue.svg)](https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

A cross-platform GUI application for flashing firmware to Snapmaker U1 3D printers with **embedded firmware** and **automatic update checking**.

## Features

- 📦 **Embedded firmware** - No browsing needed, firmware included!
- 🔄 **Auto-update checking** - Checks paxx12's repo for latest firmware on startup
- 📊 **Download progress bar** - Visual feedback during firmware downloads
- 🔀 **Base & Extended variants** - Download either firmware variant
- 🔌 **Auto-detect serial ports** - Finds your printer automatically
- 📈 **Flash progress tracking** - Real-time flash progress
- 📝 **Detailed logging** - See exactly what's happening
- ✅ **Connection testing** - Verify before flashing
- 🖥️ **Cross-platform** - Works on Windows, macOS, and Linux
- ⏱️ **Timeout protection** - Won't get stuck on network checks

## What's New in v2.2.3

### Latest Features
✨ **Proper Window Sizing** - All buttons visible immediately, no resizing needed (800x750)
✨ **Timeout Protection** - No more getting stuck on "Checking...", 15-second timeout
✨ **Download Progress Bar** - Visual feedback during firmware downloads
✨ **Base & Extended Firmware** - Download either variant from paxx12's releases
✨ **Fixed Browse Button** - File dialog opens immediately when selected

### Previous Features
✨ **Embedded Firmware** - Firmware bundled with the app, no separate download needed
✨ **GitHub Auto-Check** - Checks paxx12's repo for firmware updates on startup
✨ **Smart Version Comparison** - Compares versions and alerts on updates
✨ **Multiple Sources** - Use bundled, download latest, or browse custom firmware

## Download

### Pre-built Executables

| Platform | Download |
|----------|----------|
| Windows | [SnapmakerU1-Flasher-Windows.exe](https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher/releases/latest) |
| macOS | [SnapmakerU1-Flasher-macOS.app.zip](https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher/releases/latest) |
| Linux | [SnapmakerU1-Flasher-Linux](https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher/releases/latest) |

### Run from Source

```bash
# Clone the repository
git clone https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher.git
cd SnapmakerU1-Extended-Firmware-GUI-Flasher

# Install dependencies
pip install -r requirements.txt

# Run the application
python snapmaker_u1_flasher.py
```

## Usage

1. **Connect your printer** via USB cable
2. **Select the serial port** (auto-detected)
3. **Choose baud rate** (usually 115200 or 250000)
4. **Select firmware source:**
   - **Use Bundled** - Flash the included firmware (fastest)
   - **Browse File** - Select your own firmware file (.bin, .hex, .elf)
5. **Or download latest:** Click **"📥 Download Base"** or **"📥 Download Extended"** to download from paxx12's repo
5. **Click "Flash Firmware"**
6. **Wait for completion** - Do not disconnect!

## Credits

- **Extended Firmware:** [paxx12](https://github.com/paxx12/SnapmakerU1-Extended-Firmware)
- **Flasher Tool:** kbaker827

## License

MIT License - See [LICENSE](LICENSE) file
