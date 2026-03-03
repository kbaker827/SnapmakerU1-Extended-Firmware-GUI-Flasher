#!/usr/bin/env python3
"""
Snapmaker U1 Extended Firmware Flasher v1.1
Cross-platform GUI with embedded firmware & GitHub auto-update checking
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os, sys, platform, time, hashlib, json, re, webbrowser
import serial
import serial.tools.list_ports
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

class SnapmakerU1Flasher:
    VERSION = "2.2.0"
    APP_NAME = "Snapmaker U1 Firmware Flasher"
    
    # GitHub config - Check paxx12's repo for FIRMWARE updates
    # (The flasher app itself is at kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher)
    GITHUB_USER = "paxx12"
    GITHUB_REPO = "SnapmakerU1-Extended-Firmware"
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}"
    GITHUB_RELEASES = f"{GITHUB_API}/releases/latest"
    
    BAUD_RATES = [115200, 250000, 500000, 1000000]
    DEFAULT_BAUD = 115200
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{self.APP_NAME} v{self.VERSION}")
        self.root.geometry("800x750")
        self.root.minsize(750, 700)
        
        # Windows DPI awareness
        if sys.platform == 'win32':
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except: pass
        
        # State variables
        self.bundled_firmware_path = None
        self.bundled_firmware_version = None
        self.latest_firmware_version = None
        self.base_firmware_url = None
        self.extended_firmware_url = None
        self.needs_update = False
        self.is_flashing = False
        self.cancel_requested = False
        
        self._find_bundled_firmware()
        self.setup_ui()
        self.refresh_ports()
        self.root.after(1000, self.check_firmware_update)
    
    def _find_bundled_firmware(self):
        """Look for bundled firmware in multiple locations"""
        search_paths = [
            Path(__file__).parent / "firmware.bin",
            Path(__file__).parent / "firmware.hex",
            Path(__file__).parent / "firmware" / "firmware.bin",
            Path(getattr(sys, '_MEIPASS', '')) / "firmware.bin",  # PyInstaller
            Path.home() / ".snapmaker_u1" / "firmware.bin",
        ]
        
        for path in search_paths:
            if path.exists():
                self.bundled_firmware_path = str(path)
                self.bundled_firmware_version = self._extract_version(path)
                break
    
    def _extract_version(self, filepath):
        """Extract version from firmware filename or content"""
        filename = filepath.name if isinstance(filepath, Path) else Path(filepath).name
        
        # Try filename pattern (v1.2.3 or 1.2.3)
        match = re.search(r'v?(\d+\.\d+\.?\d*)', filename, re.IGNORECASE)
        if match:
            v = match.group(1)
            return f"v{v}" if not v.startswith('v') else v
        
        # Try reading from file header
        try:
            with open(filepath, 'rb') as f:
                header = f.read(2048).decode('utf-8', errors='ignore')
                match = re.search(r'[Vv]ersion[:\s]*(\d+\.\d+\.?\d*)', header)
                if match:
                    return f"v{match.group(1)}"
        except: pass
        
        # Fallback to file modification date
        try:
            mtime = os.path.getmtime(filepath)
            return datetime.fromtimestamp(mtime).strftime("v%Y.%m.%d")
        except:
            return "unknown"
    
    def setup_ui(self):
        main = ttk.Frame(self.root, padding="15")
        main.pack(fill=tk.BOTH, expand=True)
        
        self._create_header(main)
        self._create_firmware_section(main)
        self._create_connection_section(main)
        self._create_progress_section(main)
        self._create_log_section(main)
        self._create_buttons(main)
    
    def _create_header(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0,10))
        
        ttk.Label(header, text=f"🔧 {self.APP_NAME}", 
                 font=('Segoe UI', 16, 'bold')).pack(anchor=tk.W)
        ttk.Label(header, text=f"v{self.VERSION} | {platform.system()} {platform.machine()}", 
                 font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W)
        
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
    
    def _create_firmware_section(self, parent):
        fw = ttk.LabelFrame(parent, text="Firmware Status", padding="10")
        fw.pack(fill=tk.X, pady=(0,10))
        
        # Bundled version
        row1 = ttk.Frame(fw)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Bundled:", width=16, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.bundled_var = tk.StringVar(value=f"{self.bundled_firmware_version or 'None'} ({self._fmt_size(self.bundled_firmware_path)})")
        ttk.Label(row1, textvariable=self.bundled_var, font=('Consolas', 9)).pack(side=tk.LEFT)
        
        # Latest version
        row2 = ttk.Frame(fw)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Latest Available:", width=16, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        self.latest_var = tk.StringVar(value="Checking...")
        ttk.Label(row2, textvariable=self.latest_var, font=('Consolas', 9)).pack(side=tk.LEFT)
        
        # Status & buttons
        row3 = ttk.Frame(fw)
        row3.pack(fill=tk.X, pady=5)
        self.status_var = tk.StringVar(value="")
        self.status_lbl = ttk.Label(row3, textvariable=self.status_var, font=('Segoe UI', 9, 'bold'))
        self.status_lbl.pack(side=tk.LEFT)
        
        # Download buttons for base and extended
        self.download_base_btn = ttk.Button(row3, text="📥 Download Base",
                                            command=self.download_base, state=tk.DISABLED)
        self.download_base_btn.pack(side=tk.RIGHT)
        
        self.download_ext_btn = ttk.Button(row3, text="📥 Download Extended",
                                           command=self.download_extended, state=tk.DISABLED)
        self.download_ext_btn.pack(side=tk.RIGHT, padx=(0,5))
        
        ttk.Button(row3, text="🔄 Check", command=self.check_firmware_update).pack(side=tk.RIGHT, padx=(0,5))
        
        # Source selection
        row4 = ttk.Frame(fw)
        row4.pack(fill=tk.X, pady=(10,0))
        ttk.Label(row4, text="Flash Source:", font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        
        self.source_var = tk.StringVar(value="bundled")
        self.source_var.trace_add('write', self._on_source_change)
        
        ttk.Radiobutton(row4, text="Use Bundled", variable=self.source_var, value="bundled").pack(side=tk.LEFT, padx=(10,5))
        ttk.Radiobutton(row4, text="Browse File", variable=self.source_var, value="browse").pack(side=tk.LEFT)
        
        # Store browsed file path
        self.browsed_firmware_path = None
    
    def _create_connection_section(self, parent):
        conn = ttk.LabelFrame(parent, text="Printer Connection", padding="10")
        conn.pack(fill=tk.X, pady=(0,10))
        
        # Port
        r1 = ttk.Frame(conn)
        r1.pack(fill=tk.X, pady=2)
        ttk.Label(r1, text="Serial Port:", width=12).pack(side=tk.LEFT)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(r1, textvariable=self.port_var, state="readonly", width=35)
        self.port_combo.pack(side=tk.LEFT, padx=(5,5))
        ttk.Button(r1, text="🔄", command=self.refresh_ports, width=5).pack(side=tk.LEFT)
        
        # Baud
        r2 = ttk.Frame(conn)
        r2.pack(fill=tk.X, pady=2)
        ttk.Label(r2, text="Baud Rate:", width=12).pack(side=tk.LEFT)
        self.baud_var = tk.StringVar(value=str(self.DEFAULT_BAUD))
        ttk.Combobox(r2, textvariable=self.baud_var, values=self.BAUD_RATES, 
                    state="readonly", width=15).pack(side=tk.LEFT, padx=(5,10))
        ttk.Button(r2, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT)
    
    def _create_progress_section(self, parent):
        prog = ttk.LabelFrame(parent, text="Progress", padding="10")
        prog.pack(fill=tk.X, pady=(0,10))
        
        self.prog_status_var = tk.StringVar(value="Ready")
        ttk.Label(prog, textvariable=self.prog_status_var, font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(prog, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(10,0))
        
        self.prog_detail_var = tk.StringVar(value="")
        ttk.Label(prog, textvariable=self.prog_detail_var, 
                 font=('Consolas', 9), foreground='gray').pack(anchor=tk.W, pady=(5,0))
    
    def _create_log_section(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        
        container = ttk.Frame(log_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        scroll = ttk.Scrollbar(container)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(container, height=12, wrap=tk.WORD, 
                               font=('Consolas', 9), yscrollcommand=scroll.set, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.log_text.yview)
    
    def _create_buttons(self, parent):
        btns = ttk.Frame(parent)
        btns.pack(fill=tk.X)
        
        left = ttk.Frame(btns)
        left.pack(side=tk.LEFT)
        ttk.Button(left, text="❓ Help", command=self.show_help, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(left, text="ℹ️ About", command=self.show_about, width=10).pack(side=tk.LEFT)
        
        right = ttk.Frame(btns)
        right.pack(side=tk.RIGHT)
        self.flash_btn = ttk.Button(right, text="⚡ Flash Firmware", command=self.start_flash, width=18)
        self.flash_btn.pack(side=tk.LEFT, padx=(0,5))
        self.cancel_btn = ttk.Button(right, text="⏹ Cancel", command=self.cancel_flash, state=tk.DISABLED, width=12)
        self.cancel_btn.pack(side=tk.LEFT)
    
    def _on_source_change(self, *args):
        """Handle firmware source selection change"""
        source = self.source_var.get()
        if source == "browse":
            # Open file dialog immediately when Browse is selected
            self._browse_for_firmware()
        elif source == "bundled":
            # Clear browsed path when switching back to bundled
            self.browsed_firmware_path = None
    
    def _browse_for_firmware(self):
        """Open file dialog to browse for firmware"""
        path = filedialog.askopenfilename(
            title="Select Firmware File",
            filetypes=[
                ('Firmware files', '*.bin *.hex *.elf *.fw'),
                ('Binary files', '*.bin'),
                ('Hex files', '*.hex'),
                ('All files', '*.*')
            ]
        )
        if path:
            self.browsed_firmware_path = path
            version = self._extract_version(Path(path))
            self._log(f"Selected firmware: {path}")
            self._log(f"Version: {version}")
            # Show selected file in UI
            self.status_var.set(f"Selected: {version}")
        else:
            # User cancelled - revert to bundled
            self.source_var.set("bundled")
    
    def _fmt_size(self, path):
        if not path: return "0 B"
        try:
            sz = os.path.getsize(path)
            for u in ['B','KB','MB']:
                if sz < 1024: return f"{sz:.1f} {u}"
                sz /= 1024
            return f"{sz:.1f} GB"
        except: return "?"
    
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        plist = [f"{p.device} - {p.description}" for p in ports]
        
        if plist:
            self.port_combo['values'] = plist
            for i, p in enumerate(plist):
                if any(x in p.lower() for x in ['usb','serial','ch340','ftdi','cp210']):
                    self.port_combo.current(i)
                    break
            else:
                self.port_combo.current(0)
            self._log(f"Found {len(plist)} ports")
        else:
            self.port_combo['values'] = ['No ports found']
            self.port_combo.current(0)
            self._log("No serial ports found", "warning")
    
    def get_port(self):
        sel = self.port_var.get()
        return sel.split(' - ')[0] if ' - ' in sel else sel
    
    def check_firmware_update(self):
        self._log("Checking GitHub for firmware updates...")
        self.latest_var.set("Checking...")
        self.download_base_btn.config(state=tk.DISABLED)
        self.download_ext_btn.config(state=tk.DISABLED)
        
        # Set socket timeout for this operation
        import socket
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(15)
        
        def check():
            try:
                req = urllib.request.Request(self.GITHUB_RELEASES,
                    headers={'User-Agent': self.APP_NAME, 'Accept': 'application/vnd.github.v3+json'})
                
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode())
                
                self.latest_firmware_version = data.get('tag_name', 'unknown')
                self.base_firmware_url = None
                self.extended_firmware_url = None
                
                # Find firmware assets - look for base and extended
                for asset in data.get('assets', []):
                    name = asset.get('name', '').lower()
                    url = asset.get('browser_download_url')
                    if 'basic' in name or 'base' in name:
                        self.base_firmware_url = url
                    elif 'extended' in name:
                        self.extended_firmware_url = url
                
                # Also check release notes for firmware links
                body = data.get('body', '')
                if not self.base_firmware_url or not self.extended_firmware_url:
                    links = re.findall(r'https?://[^\s<>"]+\.(?:bin|hex|fw)', body)
                    for link in links:
                        link_lower = link.lower()
                        if 'basic' in link_lower or 'base' in link_lower:
                            if not self.base_firmware_url:
                                self.base_firmware_url = link
                        elif 'extended' in link_lower:
                            if not self.extended_firmware_url:
                                self.extended_firmware_url = link
                
                self.root.after(0, self._update_fw_status)
                
            except urllib.error.HTTPError as e:
                msg = "No releases" if e.code == 404 else f"HTTP {e.code}"
                self.root.after(0, lambda: self._check_failed(msg))
            except Exception as e:
                self.root.after(0, lambda: self._check_failed(str(e)[:40]))
            finally:
                # Reset socket timeout
                socket.setdefaulttimeout(old_timeout)
        
        threading.Thread(target=check, daemon=True).start()
    
    def _check_failed(self, msg):
        self.latest_var.set("Error")
        self.status_var.set(f"❌ {msg}")
        self.status_lbl.config(foreground='red')
        self._log(f"Update check failed: {msg}", "error")
        # Re-enable buttons if we have URLs cached
        if self.base_firmware_url:
            self.download_base_btn.config(state=tk.NORMAL)
        if self.extended_firmware_url:
            self.download_ext_btn.config(state=tk.NORMAL)
    
    def _update_fw_status(self):
        self.latest_var.set(self.latest_firmware_version or "N/A")
        
        bundled = (self.bundled_firmware_version or "0").lstrip('vV')
        latest = (self.latest_firmware_version or "0").lstrip('vV')
        
        try:
            b_parts = [int(x) for x in bundled.split('.') if x.isdigit()]
            l_parts = [int(x) for x in latest.split('.') if x.isdigit()]
            needs = tuple(l_parts) > tuple(b_parts)
        except Exception:
            needs = latest != bundled and latest != "0"
        
        self.needs_update = needs
        
        # Enable download buttons based on availability
        if self.base_firmware_url:
            self.download_base_btn.config(state=tk.NORMAL)
        else:
            self.download_base_btn.config(state=tk.DISABLED)
            
        if self.extended_firmware_url:
            self.download_ext_btn.config(state=tk.NORMAL)
        else:
            self.download_ext_btn.config(state=tk.DISABLED)
        
        if needs:
            self.status_var.set(f"⚠️ Update: v{bundled} → v{latest}")
            self.status_lbl.config(foreground='red')
            self._log(f"Update available: v{bundled} → v{latest}", "warning")
        else:
            self.status_var.set("✅ Up to date")
            self.status_lbl.config(foreground='green')
            self._log("Firmware is current")
    
    def download_base(self):
        """Download base firmware with progress tracking"""
        self._download_firmware(self.base_firmware_url, "Base")
    
    def download_extended(self):
        """Download extended firmware with progress tracking"""
        self._download_firmware(self.extended_firmware_url, "Extended")
    
    def _download_firmware(self, url, variant):
        """Download firmware with progress bar updates"""
        if not url:
            messagebox.showerror("Error", f"No download URL for {variant}")
            return
        
        self._log(f"Downloading {variant} firmware...")
        self.download_base_btn.config(state=tk.DISABLED)
        self.download_ext_btn.config(state=tk.DISABLED)
        self.prog_status_var.set(f"Downloading {variant}...")
        self.progress_var.set(0)
        
        def download():
            try:
                fw_dir = Path.home() / ".snapmaker_u1"
                fw_dir.mkdir(exist_ok=True)
                
                ext = '.bin'
                if '.hex' in url.lower(): ext = '.hex'
                elif '.fw' in url.lower(): ext = '.fw'
                
                local = fw_dir / f"firmware_{variant.lower()}_{self.latest_firmware_version}{ext}"
                
                req = urllib.request.Request(url, headers={'User-Agent': self.APP_NAME})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    chunk_size = 8192
                    
                    with open(local, 'wb') as f:
                        while True:
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress bar
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                                self.root.after(0, lambda d=downloaded, t=total_size: 
                                    self.prog_detail_var.set(f"{self._fmt_size_bytes(d)} / {self._fmt_size_bytes(t)}"))
                
                self.bundled_firmware_path = str(local)
                self.bundled_firmware_version = self.latest_firmware_version
                
                self.root.after(0, lambda: self._dl_complete(local, variant))
            except Exception as e:
                self.root.after(0, lambda: self._dl_failed(str(e)))
        
        threading.Thread(target=download, daemon=True).start()
    
    def _fmt_size_bytes(self, size):
        """Format byte size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _dl_complete(self, path, variant):
        self.bundled_var.set(f"{self.bundled_firmware_version} ({self._fmt_size(path)})")
        self.status_var.set(f"✅ {variant} Downloaded")
        self.status_lbl.config(foreground='green')
        self._log(f"{variant} firmware downloaded: {path}", "success")
        messagebox.showinfo("Success", f"{variant} firmware downloaded!\nVersion: {self.bundled_firmware_version}\nReady to flash!")
        self.prog_status_var.set("Ready")
        self.progress_var.set(100)
    
    def _dl_failed(self, err):
        self.download_base_btn.config(state=tk.NORMAL if self.base_firmware_url else tk.DISABLED)
        self.download_ext_btn.config(state=tk.NORMAL if self.extended_firmware_url else tk.DISABLED)
        self.status_var.set("❌ Download failed")
        self.status_lbl.config(foreground='red')
        self._log(f"Download failed: {err}", "error")
        messagebox.showerror("Download Failed", err)
        self.prog_status_var.set("Ready")
    
    def test_connection(self):
        port = self.get_port()
        if not port or port == 'No ports found':
            messagebox.showerror("Error", "Select a port")
            return
        
        baud = int(self.baud_var.get())
        self._log(f"Testing {port} @ {baud}...")
        self.prog_status_var.set("Testing...")
        
        try:
            ser = serial.Serial(port, baud, timeout=2)
            ser.write(b'\nM115\n')
            time.sleep(0.5)
            resp = ser.read(ser.in_waiting or 100).decode('utf-8', errors='ignore')
            ser.close()
            
            if 'FIRMWARE_NAME' in resp or 'ok' in resp.lower():
                self._log("✅ Connection OK", "success")
                messagebox.showinfo("Success", "Printer detected!")
                self.prog_status_var.set("Connected")
            else:
                self._log("⚠️ Unclear response", "warning")
                messagebox.showwarning("Warning", "Port opened but response unclear")
                self.prog_status_var.set("Unclear")
        except Exception as e:
            self._log(f"❌ Failed: {e}", "error")
            messagebox.showerror("Failed", str(e))
            self.prog_status_var.set("Failed")
    
    def start_flash(self):
        port = self.get_port()
        if not port or port == 'No ports found':
            messagebox.showerror("Error", "Select a port")
            return
        
        source = self.source_var.get()
        
        if source == "bundled":
            if not self.bundled_firmware_path or not os.path.exists(self.bundled_firmware_path):
                messagebox.showerror("Error", "No bundled firmware. Download or browse.")
                return
            fw_path = self.bundled_firmware_path
            fw_ver = self.bundled_firmware_version
                
        elif source == "browse":
            if not self.browsed_firmware_path or not os.path.exists(self.browsed_firmware_path):
                # Try to browse again if no file selected
                self._browse_for_firmware()
                if not self.browsed_firmware_path:
                    return
            fw_path = self.browsed_firmware_path
            fw_ver = self._extract_version(Path(fw_path))
        else:
            return
        
        if not messagebox.askyesno("Confirm Flash", 
            f"⚠️ Flash firmware {fw_ver}?\n\nPort: {port}\nBaud: {self.baud_var.get()}\n\n"
            "WARNING: Do not interrupt!\n\nStart?"):
            return
        
        self._run_flash(fw_path, port)
    
    def _run_flash(self, fw_path, port):
        self.is_flashing = True
        self.cancel_requested = False
        self.flash_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.prog_status_var.set("Flashing...")
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        threading.Thread(target=self._flash_thread, args=(fw_path, port), daemon=True).start()
    
    def _flash_thread(self, fw_path, port):
        ser = None
        try:
            baud = int(self.baud_var.get())
            fw_size = os.path.getsize(fw_path)

            self.root.after(0, lambda: self._log(f"Opening {port} @ {baud}..."))

            ser = serial.Serial(port, baud, timeout=1)
            self.root.after(0, lambda: self._log("Connected"))
            self.root.after(0, lambda: self._log("Entering bootloader..."))

            ser.write(b'M997\n')
            time.sleep(2)
            ser.close()
            ser = None
            time.sleep(1)

            try:
                ser = serial.Serial(port, 115200, timeout=2)
            except serial.SerialException:
                ser = serial.Serial(port, baud, timeout=2)

            self.root.after(0, lambda: self._log("Sending firmware..."))

            with open(fw_path, 'rb') as fw:
                sent = 0
                chunk_sz = 1024

                while True:
                    if self.cancel_requested:
                        self.root.after(0, lambda: self._log("Cancelled", "warning"))
                        break

                    chunk = fw.read(chunk_sz)
                    if not chunk:
                        break

                    ser.write(chunk)
                    sent += len(chunk)

                    prog = (sent / fw_size) * 100
                    detail = f"{self._fmt_size_bytes(sent)} / {self._fmt_size_bytes(fw_size)}"
                    self.root.after(0, lambda p=prog: self.progress_var.set(p))
                    self.root.after(0, lambda d=detail: self.prog_detail_var.set(d))

                    time.sleep(0.01)
                    if ser.in_waiting:
                        resp = ser.read(ser.in_waiting)
                        if b'error' in resp.lower():
                            raise Exception(f"Printer error: {resp.decode('utf-8', errors='ignore')}")

            if not self.cancel_requested:
                self.root.after(0, lambda: self._log("Verifying..."))
                time.sleep(3)
                ser.write(b'M115\n')
                time.sleep(1)
                resp = ser.read(ser.in_waiting or 100)

                if resp:
                    self.root.after(0, lambda: self._log("✅ Flash successful!", "success"))
                    self.root.after(0, lambda: self.prog_status_var.set("Complete"))
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Firmware flashed!\n\nPower cycle your printer."))
                else:
                    self.root.after(0, lambda: self._log("⚠️ Flash complete (no verify)", "warning"))
                    self.root.after(0, lambda: messagebox.showwarning("Warning", "Completed but verification unclear"))

            ser.close()
            ser = None

        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self._log(f"❌ Flash failed: {err}", "error"))
            self.root.after(0, lambda: self.prog_status_var.set("Failed"))
            self.root.after(0, lambda: messagebox.showerror("Failed", err))
        finally:
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
            self.is_flashing = False
            cancel = self.cancel_requested
            self.root.after(0, lambda: self._finish_flash(cancel))

    def _finish_flash(self, was_cancelled):
        self.flash_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        if not was_cancelled:
            self.progress_var.set(100)
    
    def cancel_flash(self):
        if self.is_flashing:
            self.cancel_requested = True
            self._log("Cancelling...")
            self.prog_status_var.set("Cancelling...")
    
    def _log(self, msg, level="info"):
        ts = time.strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{ts}] ")
        
        start = self.log_text.index("end-1c linestart")
        self.log_text.insert(tk.END, f"{msg}\n")
        end = self.log_text.index("end-1c")
        
        colors = {"info":"black", "success":"green", "warning":"orange", "error":"red"}
        tag = f"c_{level}"
        if tag not in self.log_text.tag_names():
            self.log_text.tag_config(tag, foreground=colors.get(level,"black"))
        
        self.log_text.tag_add(tag, start, end)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def show_help(self):
        txt = """SNAPMAKER U1 FIRMWARE FLASHER

QUICK START:
1. Connect printer via USB
2. Check Firmware Status for updates
3. Download latest or use bundled
4. Select port & baud rate
5. Click Flash Firmware
6. Wait - do not disconnect!

FIRMWARE SOURCES:
• Use Bundled - Use embedded or downloaded firmware
• Browse File - Select a custom firmware file

DOWNLOADING FIRMWARE:
Use the 📥 Download Base or 📥 Download Extended
buttons in the Firmware Status section to fetch the
latest release from GitHub.

AUTO-UPDATE:
Checks GitHub on startup for new releases.

SAFETY:
⚠️ Do NOT disconnect during flash
⚠️ Do NOT power off printer
⚠️ Interruption may brick device

GitHub: https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher
"""
        win = tk.Toplevel(self.root)
        win.title("Help")
        win.geometry("500x450")
        txt_widget = tk.Text(win, wrap=tk.WORD, padx=10, pady=10, font=('Consolas',10))
        txt_widget.pack(fill=tk.BOTH, expand=True)
        txt_widget.insert(1.0, txt)
        txt_widget.config(state=tk.DISABLED)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)
    
    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title("About")
        win.geometry("480x320")
        win.resizable(False, False)

        txt = tk.Text(win, wrap=tk.WORD, padx=15, pady=12,
                      font=('Segoe UI', 10), relief=tk.FLAT,
                      cursor="arrow")
        txt.pack(fill=tk.BOTH, expand=True)

        # Non-link content
        txt.insert(tk.END, f"{self.APP_NAME}\n\n", "bold")
        txt.insert(tk.END,
            f"Version:   {self.VERSION}\n"
            f"Platform:  {platform.system()} {platform.machine()}\n"
            f"Python:    {platform.python_version()}\n\n"
            f"Bundled:   {self.bundled_firmware_version or 'None'}\n"
            f"Latest:    {self.latest_firmware_version or 'Unknown'}\n\n"
            "Firmware repo:  ")

        # Firmware repo link
        fw_url = f"https://github.com/{self.GITHUB_USER}/{self.GITHUB_REPO}"
        txt.insert(tk.END, fw_url, "link_fw")

        txt.insert(tk.END, "\nFlasher app:    ")

        # Flasher app repo link
        app_url = "https://github.com/kbaker827/SnapmakerU1-Extended-Firmware-GUI-Flasher"
        txt.insert(tk.END, app_url, "link_app")

        txt.insert(tk.END, "\n\nLicense: MIT\n")

        # Tag styling
        txt.tag_config("bold", font=('Segoe UI', 11, 'bold'))
        txt.tag_config("link_fw",  foreground="#0066cc", underline=True, font=('Segoe UI', 10))
        txt.tag_config("link_app", foreground="#0066cc", underline=True, font=('Segoe UI', 10))

        # Click bindings
        txt.tag_bind("link_fw",  "<Button-1>", lambda e: webbrowser.open(fw_url))
        txt.tag_bind("link_app", "<Button-1>", lambda e: webbrowser.open(app_url))

        # Cursor changes on hover
        txt.tag_bind("link_fw",  "<Enter>", lambda e: txt.config(cursor="hand2"))
        txt.tag_bind("link_fw",  "<Leave>", lambda e: txt.config(cursor="arrow"))
        txt.tag_bind("link_app", "<Enter>", lambda e: txt.config(cursor="hand2"))
        txt.tag_bind("link_app", "<Leave>", lambda e: txt.config(cursor="arrow"))

        txt.config(state=tk.DISABLED)
        ttk.Button(win, text="Close", command=win.destroy).pack(pady=10)
    
    def run(self):
        self._log(f"{self.APP_NAME} v{self.VERSION} started")
        self._log(f"Platform: {platform.system()}")
        if self.bundled_firmware_path:
            self._log(f"Bundled: {self.bundled_firmware_version}")
        self.root.mainloop()


if __name__ == '__main__':
    app = SnapmakerU1Flasher()
    app.run()
