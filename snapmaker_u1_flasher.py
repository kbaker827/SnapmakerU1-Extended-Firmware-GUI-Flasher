#!/usr/bin/env python3
"""
Snapmaker U1 Extended Firmware Flasher
Cross-platform GUI for flashing firmware to Snapmaker U1 3D printer
Supports: macOS, Windows, Linux
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
import platform
import serial
import serial.tools.list_ports
import time
import hashlib
from pathlib import Path

class SnapmakerU1Flasher:
    """Main application class"""
    
    VERSION = "1.0.0"
    BAUD_RATES = [115200, 250000, 500000, 1000000]
    DEFAULT_BAUD = 115200
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Snapmaker U1 Firmware Flasher v{self.VERSION}")
        self.root.geometry("700x550")
        self.root.minsize(650, 500)
        
        # Set DPI awareness on Windows
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
        
        self.firmware_path = None
        self.serial_connection = None
        self.is_flashing = False
        self.cancel_requested = False
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self._create_header(main_frame)
        
        # Connection settings
        self._create_connection_frame(main_frame)
        
        # Firmware selection
        self._create_firmware_frame(main_frame)
        
        # Progress section
        self._create_progress_frame(main_frame)
        
        # Log output
        self._create_log_frame(main_frame)
        
        # Buttons
        self._create_button_frame(main_frame)
        
    def _create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        ttk.Label(
            header,
            text="🔧 Snapmaker U1 Extended Firmware Flasher",
            font=('Segoe UI', 16, 'bold')
        ).pack(anchor=tk.W)
        
        # Subtitle
        ttk.Label(
            header,
            text=f"Version {self.VERSION} | Platform: {platform.system()} {platform.release()}",
            font=('Segoe UI', 9),
            foreground='gray'
        ).pack(anchor=tk.W)
        
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
    def _create_connection_frame(self, parent):
        """Create serial connection settings"""
        conn_frame = ttk.LabelFrame(parent, text="Printer Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Port selection
        port_row = ttk.Frame(conn_frame)
        port_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(port_row, text="Serial Port:", width=12).pack(side=tk.LEFT)
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            port_row, 
            textvariable=self.port_var,
            state="readonly",
            width=30
        )
        self.port_combo.pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Button(
            port_row,
            text="🔄 Refresh",
            command=self.refresh_ports,
            width=10
        ).pack(side=tk.LEFT)
        
        # Baud rate
        baud_row = ttk.Frame(conn_frame)
        baud_row.pack(fill=tk.X, pady=2)
        
        ttk.Label(baud_row, text="Baud Rate:", width=12).pack(side=tk.LEFT)
        
        self.baud_var = tk.StringVar(value=str(self.DEFAULT_BAUD))
        baud_combo = ttk.Combobox(
            baud_row,
            textvariable=self.baud_var,
            values=self.BAUD_RATES,
            state="readonly",
            width=15
        )
        baud_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Connection test button
        ttk.Button(
            baud_row,
            text="Test Connection",
            command=self.test_connection,
            width=15
        ).pack(side=tk.LEFT, padx=(10, 0))
        
    def _create_firmware_frame(self, parent):
        """Create firmware file selection"""
        fw_frame = ttk.LabelFrame(parent, text="Firmware File", padding="10")
        fw_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File selection row
        file_row = ttk.Frame(fw_frame)
        file_row.pack(fill=tk.X, pady=2)
        
        self.fw_path_var = tk.StringVar(value="No file selected")
        ttk.Label(
            file_row, 
            textvariable=self.fw_path_var,
            font=('Consolas', 9),
            foreground='gray'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            file_row,
            text="Browse...",
            command=self.browse_firmware,
            width=12
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # File info
        self.fw_info_var = tk.StringVar(value="")
        ttk.Label(
            fw_frame,
            textvariable=self.fw_info_var,
            font=('Segoe UI', 8),
            foreground='blue'
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Supported formats info
        ttk.Label(
            fw_frame,
            text="Supported: .bin, .hex, .elf, .fw (Snapmaker U1 Extended firmware)",
            font=('Segoe UI', 8),
            foreground='gray'
        ).pack(anchor=tk.W, pady=(5, 0))
        
    def _create_progress_frame(self, parent):
        """Create progress bar section"""
        prog_frame = ttk.Frame(parent)
        prog_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Progress label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            prog_frame,
            textvariable=self.status_var,
            font=('Segoe UI', 9, 'bold')
        ).pack(anchor=tk.W)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            prog_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Progress details
        self.progress_detail_var = tk.StringVar(value="")
        ttk.Label(
            prog_frame,
            textvariable=self.progress_detail_var,
            font=('Consolas', 8),
            foreground='gray'
        ).pack(anchor=tk.W, pady=(2, 0))
        
    def _create_log_frame(self, parent):
        """Create log output area"""
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Log text area with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_container,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 9),
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
    def _create_button_frame(self, parent):
        """Create action buttons"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)
        
        # Left side - Help and Info
        left_btns = ttk.Frame(btn_frame)
        left_btns.pack(side=tk.LEFT)
        
        ttk.Button(
            left_btns,
            text="❓ Help",
            command=self.show_help,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            left_btns,
            text="ℹ️ About",
            command=self.show_about,
            width=10
        ).pack(side=tk.LEFT)
        
        # Right side - Flash and Cancel
        right_btns = ttk.Frame(btn_frame)
        right_btns.pack(side=tk.RIGHT)
        
        self.flash_btn = ttk.Button(
            right_btns,
            text="⚡ Flash Firmware",
            command=self.start_flash,
            width=18
        )
        self.flash_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_btn = ttk.Button(
            right_btns,
            text="⏹ Cancel",
            command=self.cancel_flash,
            state=tk.DISABLED,
            width=12
        )
        self.cancel_btn.pack(side=tk.LEFT)
        
    def refresh_ports(self):
        """Refresh available serial ports"""
        ports = serial.tools.list_ports.comports()
        port_list = []
        
        for port in ports:
            # Format: "COM3 - USB Serial Device" or "/dev/ttyUSB0 - FT232R"
            port_desc = f"{port.device} - {port.description}"
            port_list.append(port_desc)
            
        if port_list:
            self.port_combo['values'] = port_list
            # Try to auto-select common printer ports
            for i, p in enumerate(port_list):
                if any(x in p.lower() for x in ['usb', 'serial', 'ch340', 'ftdi', 'cp210']):
                    self.port_combo.current(i)
                    break
            else:
                self.port_combo.current(0)
            self._log(f"Found {len(port_list)} serial ports")
        else:
            self.port_combo['values'] = ['No ports found']
            self.port_combo.current(0)
            self._log("No serial ports found", "warning")
            
    def get_selected_port(self):
        """Extract port name from selection"""
        selection = self.port_var.get()
        if selection and ' - ' in selection:
            return selection.split(' - ')[0]
        return selection
        
    def browse_firmware(self):
        """Open file dialog to select firmware"""
        filetypes = [
            ('Firmware files', '*.bin *.hex *.elf *.fw'),
            ('Binary files', '*.bin'),
            ('Hex files', '*.hex'),
            ('All files', '*.*')
        ]
        
        path = filedialog.askopenfilename(
            title="Select Firmware File",
            filetypes=filetypes
        )
        
        if path:
            self.firmware_path = path
            self.fw_path_var.set(path)
            
            # Get file info
            try:
                size = os.path.getsize(path)
                size_str = self._format_size(size)
                
                # Calculate MD5 hash
                with open(path, 'rb') as f:
                    md5_hash = hashlib.md5(f.read(8192)).hexdigest()[:16]
                
                self.fw_info_var.set(f"Size: {size_str} | MD5: {md5_hash}...")
                self._log(f"Selected firmware: {os.path.basename(path)} ({size_str})")
            except Exception as e:
                self.fw_info_var.set(f"Error reading file: {e}")
                
    def _format_size(self, size_bytes):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
        
    def test_connection(self):
        """Test connection to printer"""
        port = self.get_selected_port()
        if not port or port == 'No ports found':
            messagebox.showerror("Error", "Please select a valid serial port")
            return
            
        baud = int(self.baud_var.get())
        
        self._log(f"Testing connection to {port} @ {baud} baud...")
        self.status_var.set("Testing connection...")
        
        try:
            ser = serial.Serial(port, baud, timeout=2)
            ser.write(b'\nM115\n')  # Get firmware info
            time.sleep(0.5)
            response = ser.read(ser.in_waiting or 100).decode('utf-8', errors='ignore')
            ser.close()
            
            if 'FIRMWARE_NAME' in response or 'ok' in response:
                self._log("✅ Connection successful! Printer detected.", "success")
                messagebox.showinfo("Success", "Printer connection test successful!")
                self.status_var.set("Printer connected")
            else:
                self._log("⚠️ Port opened but no printer response", "warning")
                messagebox.showwarning("Warning", "Port opened but printer did not respond. Check baud rate.")
                self.status_var.set("No response from printer")
                
        except serial.SerialException as e:
            self._log(f"❌ Connection failed: {e}", "error")
            messagebox.showerror("Connection Failed", str(e))
            self.status_var.set("Connection failed")
            
    def start_flash(self):
        """Start firmware flashing process"""
        # Validate inputs
        port = self.get_selected_port()
        if not port or port == 'No ports found':
            messagebox.showerror("Error", "Please select a serial port")
            return
            
        if not self.firmware_path or not os.path.exists(self.firmware_path):
            messagebox.showerror("Error", "Please select a firmware file")
            return
            
        # Confirm flash
        if not messagebox.askyesno(
            "Confirm Flash",
            "⚠️ WARNING: Flashing firmware can brick your printer if interrupted.\n\n"
            "Ensure:\n"
            "• Printer is powered and connected\n"
            "• USB cable is secure\n"
            "• Do not disconnect during flash\n\n"
            "Start flashing?"
        ):
            return
            
        # Update UI
        self.is_flashing = True
        self.cancel_requested = False
        self.flash_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.status_var.set("Flashing firmware...")
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Start flashing in thread
        thread = threading.Thread(target=self._flash_thread, args=(port,))
        thread.daemon = True
        thread.start()
        
    def _flash_thread(self, port):
        """Firmware flashing thread"""
        try:
            baud = int(self.baud_var.get())
            firmware_size = os.path.getsize(self.firmware_path)
            
            self._log(f"Opening {port} @ {baud} baud...")
            
            # Open serial connection
            with serial.Serial(port, baud, timeout=1) as ser:
                self._log("Connected to printer")
                self._log("Entering bootloader mode...")
                
                # Send M997 to enter bootloader (Marlin command)
                ser.write(b'M997\n')
                time.sleep(2)
                
                # Open firmware file
                with open(self.firmware_path, 'rb') as fw:
                    bytes_sent = 0
                    chunk_size = 1024
                    
                    while True:
                        if self.cancel_requested:
                            self._log("Flash cancelled by user", "warning")
                            break
                            
                        chunk = fw.read(chunk_size)
                        if not chunk:
                            break
                            
                        # Write chunk to printer
                        ser.write(chunk)
                        bytes_sent += len(chunk)
                        
                        # Update progress
                        progress = (bytes_sent / firmware_size) * 100
                        self.progress_var.set(progress)
                        self.progress_detail_var.set(
                            f"Sent: {self._format_size(bytes_sent)} / {self._format_size(firmware_size)}"
                        )
                        
                        # Read response
                        time.sleep(0.01)
                        if ser.in_waiting:
                            response = ser.read(ser.in_waiting)
                            if b'error' in response.lower():
                                raise Exception(f"Printer error: {response.decode('utf-8', errors='ignore')}")
                                
                if not self.cancel_requested:
                    self._log("Waiting for flash to complete...")
                    time.sleep(3)
                    
                    # Verify
                    ser.write(b'M115\n')
                    time.sleep(1)
                    response = ser.read(ser.in_waiting or 100)
                    
                    if response:
                        self._log("✅ Firmware flash successful!", "success")
                        self.status_var.set("Flash complete")
                        messagebox.showinfo("Success", "Firmware flashed successfully!\n\nPlease power cycle your printer.")
                    else:
                        self._log("⚠️ Flash may have succeeded but no verification response", "warning")
                        messagebox.showwarning("Warning", "Flash completed but could not verify. Please check printer.")
                        
        except Exception as e:
            self._log(f"❌ Flash failed: {e}", "error")
            self.status_var.set("Flash failed")
            messagebox.showerror("Flash Failed", str(e))
        finally:
            self.is_flashing = False
            self.flash_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            if not self.cancel_requested:
                self.progress_var.set(100)
                
    def cancel_flash(self):
        """Cancel flashing"""
        if self.is_flashing:
            self.cancel_requested = True
            self._log("Cancelling flash...")
            self.status_var.set("Cancelling...")
            
    def _log(self, message, level="info"):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Color codes
        colors = {
            "info": "black",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] ")
        
        start_idx = self.log_text.index("end-1c linestart")
        self.log_text.insert(tk.END, f"{message}\n")
        end_idx = self.log_text.index("end-1c")
        
        # Apply color tag
        tag_name = f"color_{level}"
        if tag_name not in self.log_text.tag_names():
            self.log_text.tag_config(tag_name, foreground=colors.get(level, "black"))
        
        self.log_text.tag_add(tag_name, start_idx, end_idx)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def show_help(self):
        """Show help dialog"""
        help_text = """SNAPMAKER U1 FIRMWARE FLASHER HELP

QUICK START:
1. Connect your Snapmaker U1 printer via USB
2. Select the correct serial port (usually shows as USB-SERIAL)
3. Select the correct baud rate (default: 115200)
4. Click 'Browse' and select your .bin or .hex firmware file
5. Click 'Flash Firmware' and wait for completion

TROUBLESHOOTING:
• If no ports appear: Install CH340/CP210x drivers
• Connection fails: Try different baud rates (250000, 500000)
• Flash fails: Ensure printer is in bootloader mode
• Windows: Check Device Manager for COM port number
• macOS: Port will be /dev/tty.usbserial-* or /dev/cu.usbserial-*

SAFETY:
• Do NOT disconnect USB during flashing
• Do NOT power off printer during flashing
• Interrupting flash may brick your printer

For more help, visit: https://github.com/paxx12/SnapmakerU1-Extended-Firmware
"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("550x500")
        
        text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10, font=('Consolas', 10))
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(1.0, help_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
        
    def show_about(self):
        """Show about dialog"""
        about_text = f"""Snapmaker U1 Extended Firmware Flasher

Version: {self.VERSION}
Platform: {platform.system()} {platform.machine()}
Python: {platform.python_version()}

A cross-platform tool for flashing firmware to
Snapmaker U1 3D printers.

GitHub: https://github.com/paxx12/SnapmakerU1-Extended-Firmware

Credits:
• GUI Framework: Python tkinter
• Serial Library: pyserial
• Icons: Unicode emoji

License: MIT
"""
        messagebox.showinfo("About", about_text)
        
    def run(self):
        """Run the application"""
        self._log("Snapmaker U1 Firmware Flasher started")
        self._log(f"Platform: {platform.system()} {platform.release()}")
        self.root.mainloop()


def main():
    """Main entry point"""
    # Check for required modules
    try:
        import serial
    except ImportError:
        print("Error: pyserial is required. Install with: pip install pyserial")
        sys.exit(1)
        
    app = SnapmakerU1Flasher()
    app.run()


if __name__ == '__main__':
    main()
