# Snapmaker U1 Extended Firmware Flasher

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

A cross-platform GUI application for flashing firmware to Snapmaker U1 3D printers with **embedded firmware** and **automatic update checking**.

![Screenshot](screenshot.png)

## Features

- 📦 **Embedded firmware** - No browsing needed, firmware included!
- 🔄 **Auto-update checking** - Checks GitHub for latest firmware on startup
- 📥 **One-click updates** - Download and flash latest firmware automatically
- 🔌 **Auto-detect serial ports** - Finds your printer automatically
- 📊 **Progress tracking** - Real-time flash progress
- 📝 **Detailed logging** - See exactly what's happening
- ✅ **Connection testing** - Verify before flashing
- 🖥️ **Cross-platform** - Works on Windows, macOS, and Linux

## What's New in v1.1.0

✨ **Embedded Firmware** - Firmware bundled with the app, no separate download needed
✨ **GitHub Auto-Check** - Automatically checks for firmware updates on startup
✨ **Smart Version Comparison** - Alerts you when newer firmware is available
✨ **Download & Flash** - One-click download latest firmware and flash
✨ **Multiple Sources** - Choose bundled, download latest, or browse custom firmware

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

The app will automatically check GitHub for firmware updates on startup!

## Requirements

### Windows
- Windows 10 or later
- CH340/CP210x USB driver (usually auto-installed)

### macOS
- macOS 10.14 (Mojave) or later
- Python 3.7+ (if running from source)

### Linux
- Python 3.7+
- `python3-tk` package
- Serial port permissions

## Usage

### Quick Start (Embedded Firmware)

1. **Connect your printer** via USB cable
2. **Select the serial port** (auto-detected)
3. **Choose baud rate** (usually 115200 or 250000)
4. **Select firmware source:**
   - **Use Bundled** - Flash the included firmware (fastest)
   - **Download Latest** - Check GitHub and flash newest version
   - **Browse File** - Select your own firmware file (.bin, .hex, .elf)
5. **Click "Flash Firmware"**
6. **Wait for completion** - Do not disconnect!

### Auto-Update Workflow

1. Launch the app - it checks GitHub automatically
2. If update available, you'll see: **⚠️ Update available! v1.0 → v1.1**
3. Click **"📥 Download Latest"** to download new firmware
4. Or select **"Download Latest"** source and click **"Flash Firmware"** to download & flash in one step!

## Building from Source

### Windows (EXE)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico snapmaker_u1_flasher.py
```

### macOS (App)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.icns snapmaker_u1_flasher.py
```

### Linux (Binary)
```bash
pip install pyinstaller
pyinstaller --onefile snapmaker_u1_flasher.py
```

## Troubleshooting

### "No serial ports found"
- Install CH340 or CP210x drivers
- Try different USB cable
- Check Device Manager (Windows) or System Information (macOS)

### "Connection failed"
- Verify correct baud rate (try 115200, 250000, 500000)
- Ensure printer is powered on
- Check USB cable connection

### "Flash failed"
- Do not disconnect USB during flash
- Ensure sufficient power supply
- Try entering bootloader mode manually

## Safety Warnings

⚠️ **IMPORTANT**: Flashing firmware can brick your printer if interrupted.

- Keep USB cable connected during entire process
- Do not power off printer during flash
- Use reliable USB cable and port
- Ensure stable power supply

## Contributing

Pull requests welcome! Please ensure:
- Code follows PEP 8 style
- Tested on your platform
- Update documentation as needed

## License

MIT License - See [LICENSE](LICENSE) file

## Credits

- Original firmware: Snapmaker Team
- GUI Framework: Python tkinter
- Serial Library: pyserial
- Created by: paxx12

## Bundling Firmware with Executable

When building executables, you can bundle firmware:

**PyInstaller:**
```bash
pyinstaller --onefile --windowed \
  --add-data "firmware.bin:." \
  snapmaker_u1_flasher.py
```

The app searches for firmware in:
- Same directory as executable
- `firmware/` subdirectory  
- `~/.snapmaker_u1/` user directory
- PyInstaller `_MEIPASS` temp folder

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher/issues
- Discussions: https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher/discussions

---

**Disclaimer**: This tool is not officially affiliated with Snapmaker. Use at your own risk.
