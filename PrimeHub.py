import os
import sys
import time
import random
import shutil
import urllib.request
import threading
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import psutil
import json

# ==========================================
# DEBUG LOGGING HELPER
# ==========================================
DEBUG = False

def log_debug(message):
    if DEBUG:
        try:
            with open("c:\\Users\\Admin\\Documents\\debug.txt", "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        except Exception as e:
            print(f"Failed to log: {e}")

log_debug("Script started.")

# ==========================================
# ADMIN PRIVILEGES CHECK & SELF-ELEVATION
# ==========================================
def is_admin():
    try:
        res = ctypes.windll.shell32.IsUserAnAdmin()
        log_debug(f"IsUserAnAdmin check: {res}")
        return res != 0
    except Exception as e:
        log_debug(f"Error in is_admin: {e}")
        return False

def run_as_admin():
    if not is_admin():
        log_debug("Not running as admin. Triggering elevation...")
        script_path = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        log_debug(f"Executing: ShellExecuteW runas {sys.executable} '{script_path}' {params}")
        # Execute script as Administrator
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script_path}" {params}', None, 1
        )
        log_debug("Elevation triggered. Exiting current process.")
        sys.exit(0)
    else:
        log_debug("Already running as administrator. Proceeding.")

# Run UAC elevation check immediately
run_as_admin()

# ==========================================
# PATH SOLVER FOR BUNDLED ASSETS (PyInstaller)
# ==========================================
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)

# ==========================================
# CONFIG & PROFILE MANAGER (PERSISTENT DATA)
# ==========================================
CONFIG_FILE = "c:\\Users\\Admin\\Documents\\config.json"

DEFAULT_PROFILE = {
    "autopot_hp_enabled": False,
    "autopot_mp_enabled": False,
    "autopot_hp_key": "1",
    "autopot_mp_key": "2",
    "autopot_hp_cooldown": 2.0,
    "autopot_mp_cooldown": 2.0,
    "hp_pixel_x": 0,
    "hp_pixel_y": 0,
    "hp_pixel_r": 0,
    "mp_pixel_x": 0,
    "mp_pixel_y": 0,
    "mp_pixel_b": 0,
    "click_speed": 100,
    "click_button": "Left",
    
    # Advanced calib/state detection attributes
    "town_pixel_x": 0,
    "town_pixel_y": 0,
    "town_pixel_r": 0,
    "town_pixel_g": 0,
    "town_pixel_b": 0,
    "town_pixel_enabled": False,
    
    "auto_rejuv_enabled": False,
    "rejuv_key": "3",
    "rejuv_trigger_pct": 35,
    "auto_esc_enabled": False,
    "esc_trigger_pct": 10,
    "streamer_mode": False
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_data = {
            "license_active": False,
            "license_key": "",
            "current_profile": "PvP",
            "profiles": {
                "PvP": DEFAULT_PROFILE.copy(),
                "MF": DEFAULT_PROFILE.copy(),
                "Rush": DEFAULT_PROFILE.copy()
            }
        }
        save_config(default_data)
        return default_data
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "license_active" not in data: data["license_active"] = False
            if "license_key" not in data: data["license_key"] = ""
            if "current_profile" not in data: data["current_profile"] = "PvP"
            if "profiles" not in data: data["profiles"] = {}
            for p in ["PvP", "MF", "Rush"]:
                if p not in data["profiles"]:
                    data["profiles"][p] = DEFAULT_PROFILE.copy()
                else:
                    for k, v in DEFAULT_PROFILE.items():
                        if k not in data["profiles"][p]:
                            data["profiles"][p][k] = v
            return data
    except Exception as e:
        log_debug(f"Error loading config: {e}")
        return {
            "license_active": False,
            "license_key": "",
            "current_profile": "PvP",
            "profiles": {"PvP": DEFAULT_PROFILE.copy(), "MF": DEFAULT_PROFILE.copy(), "Rush": DEFAULT_PROFILE.copy()}
        }

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        log_debug(f"Error saving config: {e}")

# ==========================================
# CONFIGURATION & GLOBAL VARIABLES
# ==========================================
base_path = os.path.abspath(".") + os.sep
game_exe = "PrimeDiablo.exe"

img_url = "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/kakashi.jpg"
img_path = resource_path("kakashi.jpg")

ico_url = "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/kakashi_icon.ico"
ico_path = resource_path("kakashi_icon.ico")

fundo_url = "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/fundo.png"
fundo_path = resource_path("fundo.png")

cfgs = {
    "BH_elite.cfg": "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/BH_elite.cfg",
    "BH_mf.cfg": "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/BH_mf.cfg",
    "BH_rw.cfg": "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/BH_rw.cfg",
    "BH_rwall.cfg": "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/BH_rwall.cfg",
    "BH_settings.cfg": "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/BH_settings.cfg",
    "BH_normal.cfg": "https://raw.githubusercontent.com/ghkusanagy-hub/KakashiHub/main/BH_normal.cfg"
}

# Global configuration flags
SOUNDS_ENABLED = True
PARTICLES_ENABLED = True

# WinAPI Key Event Structs for robust DirectX key injection (SendInput)
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUT_UNION),
    ]

INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
VK_MENU = 0x12  # ALT key
VK_R = 0x52

# Mouse inputs for auto clicker
INPUT_MOUSE = 0
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

def click_mouse(button='left'):
    if button.lower() == 'left':
        down = MOUSEEVENTF_LEFTDOWN
        up = MOUSEEVENTF_LEFTUP
    else:
        down = MOUSEEVENTF_RIGHTDOWN
        up = MOUSEEVENTF_RIGHTUP

    try:
        # Press
        mi_down = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=down, time=0, dwExtraInfo=None)
        inp_down = INPUT(type=INPUT_MOUSE, u=INPUT_UNION(mi=mi_down))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(inp_down))
        
        time.sleep(0.01)
        
        # Release
        mi_up = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=up, time=0, dwExtraInfo=None)
        inp_up = INPUT(type=INPUT_MOUSE, u=INPUT_UNION(mi=mi_up))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(inp_up))
    except Exception as e:
        log_debug(f"Click mouse error: {e}")

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_pos():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def get_pixel_color(x, y):
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        color = ctypes.windll.gdi32.GetPixel(hdc, x, y)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        r = color & 0xff
        g = (color >> 8) & 0xff
        b = (color >> 16) & 0xff
        return r, g, b
    except Exception as e:
        log_debug(f"Error getting pixel color: {e}")
        return 0, 0, 0

def is_game_active():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return False
        buf = ctypes.create_unicode_buffer(255)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 255)
        title = buf.value.lower()
        
        buf_class = ctypes.create_unicode_buffer(255)
        ctypes.windll.user32.GetClassNameW(hwnd, buf_class, 255)
        class_name = buf_class.value.lower()
        
        return (any(kw in title for kw in ["diablo", "d2r", "bh", "companion", "game.exe", "game"]) or 
                any(kw in class_name for kw in ["diablo ii", "direct3dwindowclass"]))
    except:
        return False

def send_pot_key(key_char):
    try:
        key_char = str(key_char).upper()
        if len(key_char) == 1:
            vk = ord(key_char)
        else:
            vk = ord('1')
        press_key(vk)
        time.sleep(0.02)
        release_key(vk)
    except Exception as e:
        log_debug(f"Error sending pot key: {e}")

def press_key(vk_code):
    scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
    ki = KEYBDINPUT(wVk=0, wScan=scan_code, dwFlags=KEYEVENTF_SCANCODE, time=0, dwExtraInfo=None)
    inp = INPUT(type=INPUT_KEYBOARD, u=INPUT_UNION(ki=ki))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def release_key(vk_code):
    scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
    ki = KEYBDINPUT(wVk=0, wScan=scan_code, dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
    inp = INPUT(type=INPUT_KEYBOARD, u=INPUT_UNION(ki=ki))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def send_alt_r():
    log_debug("Sending Alt+R key event to game window.")
    press_key(VK_MENU)
    time.sleep(0.05)
    press_key(VK_R)
    time.sleep(0.05)
    release_key(VK_R)
    time.sleep(0.05)
    release_key(VK_MENU)

def send_esc_key():
    try:
        press_key(0x1B) # VK_ESCAPE = 0x1B
        time.sleep(0.02)
        release_key(0x1B)
    except Exception as e:
        log_debug(f"Error sending ESC key: {e}")

# Windows Work Area Calculator (ignoring Taskbar)
def get_work_area():
    rect = wintypes.RECT()
    if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0): # SPI_GETWORKAREA = 48
        return rect.left, rect.top, rect.right, rect.bottom
    else:
        # Fallback to absolute screen size
        user32 = ctypes.windll.user32
        return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# Bring game window to foreground (supporting list of process names for compatibility)
def activate_window_by_process_name(proc_names):
    if isinstance(proc_names, str):
        proc_names = [proc_names]
        
    pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name_lower = proc.info['name'].lower()
            if any(p.lower() == name_lower for p in proc_names):
                pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    log_debug(f"PIDs found for processes {proc_names}: {pids}")
    
    user32 = ctypes.windll.user32
    candidates = []
    
    def enum_cb(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            lp_pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
            
            # Title
            buf_title = ctypes.create_unicode_buffer(255)
            user32.GetWindowTextW(hwnd, buf_title, 255)
            title = buf_title.value
            title_lower = title.lower()
            
            # Class
            buf_class = ctypes.create_unicode_buffer(255)
            user32.GetClassNameW(hwnd, buf_class, 255)
            class_name = buf_class.value
            class_name_lower = class_name.lower()
            
            # Skip empty window titles
            if not title:
                return True
                
            score = 0
            # If the process matches our PID list, give it high priority
            if pids and lp_pid.value in pids:
                score += 200
                
            # Filter out known non-game window titles
            if any(kw in title_lower for kw in ["launcher", "loader", "setup", "config", "tool"]):
                score -= 100
                
            # Add points for window class and text matching typical game properties
            if class_name_lower == "diablo ii" or class_name_lower == "direct3dwindowclass":
                score += 300
            elif "diablo" in title_lower or "d2r" in title_lower:
                score += 150
            elif "game.exe" in title_lower or "game" in title_lower:
                score += 80
                
            if score > 0:
                candidates.append((score, hwnd, lp_pid.value, title, class_name))
        return True
        
    enum_cb_func = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(enum_cb)
    user32.EnumWindows(enum_cb_func, 0)
    
    # Sort candidates by score descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    log_debug(f"Window candidates found: {candidates}")
    
    hwnd_to_activate = None
    if candidates:
        hwnd_to_activate = candidates[0][1]
        best_pid = candidates[0][2]
        best_title = candidates[0][3]
        log_debug(f"Best window candidate: {best_title} (PID: {best_pid}) with score {candidates[0][0]}")
        
    if hwnd_to_activate:
        # Restore window if minimized
        if user32.IsIconic(hwnd_to_activate):
            user32.ShowWindow(hwnd_to_activate, 9)  # SW_RESTORE
            time.sleep(0.15)
            
        # Try multiple methods to activate foreground
        try:
            user32.SwitchToThisWindow(hwnd_to_activate, True)
            time.sleep(0.05)
        except Exception as e:
            log_debug(f"SwitchToThisWindow failed: {e}")
            
        try:
            kernel32 = ctypes.windll.kernel32
            fore_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
            curr_thread = kernel32.GetCurrentThreadId()
            user32.AttachThreadInput(curr_thread, fore_thread, True)
            
            user32.SetForegroundWindow(hwnd_to_activate)
            user32.SetActiveWindow(hwnd_to_activate)
            
            user32.AttachThreadInput(curr_thread, fore_thread, False)
        except Exception as e:
            log_debug(f"SetForegroundWindow via AttachThreadInput failed: {e}")
            
        user32.ShowWindow(hwnd_to_activate, 5) # SW_SHOW
        
        # Verify focus
        time.sleep(0.15)
        if user32.GetForegroundWindow() == hwnd_to_activate:
            log_debug("Successfully focused game window.")
            return True
        else:
            log_debug("Verification failed. Forcing activation using Alt key menu tap...")
            user32.keybd_event(0x12, 0, 0, 0) # ALT down
            user32.SetForegroundWindow(hwnd_to_activate)
            user32.keybd_event(0x12, 0, 2, 0) # ALT up
            time.sleep(0.1)
            return user32.GetForegroundWindow() == hwnd_to_activate
            
    return False

# ==========================================
# ASSET DOWNLOADER & SYNC (with User-Agent & Timeout)
# ==========================================
def download_file(url, path, timeout=5):
    try:
        log_debug(f"Downloading {url} -> {path} (timeout={timeout}s)")
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(path, 'wb') as out_file:
                out_file.write(response.read())
        log_debug(f"Download complete: {path}")
        return True
    except Exception as e:
        log_debug(f"Error downloading {url} to {path}: {e}")
        return False

# ==========================================
# AUDIO FEEDBACK HELPER
# ==========================================
def play_cyberpunk_beep(sound_type="success"):
    if not SOUNDS_ENABLED:
        return
    def run_sound():
        try:
            if sound_type == "success":
                # Double high beep
                ctypes.windll.kernel32.Beep(880, 50)
                time.sleep(0.02)
                ctypes.windll.kernel32.Beep(1760, 60)
            elif sound_type == "click":
                # Fast sharp click
                ctypes.windll.kernel32.Beep(1200, 30)
            elif sound_type == "fail":
                # Low warning buzz
                ctypes.windll.kernel32.Beep(220, 250)
        except:
            pass
    threading.Thread(target=run_sound, daemon=True).start()

# ==========================================
# LOADER SPLASH SCREEN
# ==========================================
class LoaderWindow:
    def __init__(self):
        log_debug("Initializing LoaderWindow UI...")
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#000000")
        
        # Center loader on screen
        w, h = 260, 110
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Background Image (fundo.png)
        self.bg_photo = None
        if os.path.exists(fundo_path):
            try:
                bg_img = Image.open(fundo_path).resize((w, h))
                self.bg_photo = ImageTk.PhotoImage(bg_img)
                self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
            except Exception as e:
                log_debug(f"Loader fundo.png load exception: {e}")
                
        # Logo/Icon Loader
        self.icon_photo = None
        self.icon_item = None
        if os.path.exists(ico_path):
            try:
                icon_img = Image.open(ico_path).resize((40, 40))
                self.icon_photo = ImageTk.PhotoImage(icon_img)
                self.icon_item = self.canvas.create_image(50, 30, image=self.icon_photo, anchor="center")
            except Exception as e:
                log_debug(f"Loader ico load exception: {e}")
                
        # Texts
        self.canvas.create_text(75, 28, text="Kakashi Hub", fill="#ffffff", font=("Yu Gothic UI", 14, "bold"), anchor="w")
        self.status_item = self.canvas.create_text(130, 65, text="Iniciando...", fill="#ffffff", font=("Yu Gothic UI", 9, "bold"), anchor="center")
        
        # Custom Progress Bar
        self.progress_bg = self.canvas.create_rectangle(20, 85, 240, 93, fill="#222222", width=0)
        self.progress_bar = self.canvas.create_rectangle(20, 85, 20, 93, fill="#550000", width=0)
        
        self.load_pos = 0
        self.is_done = False
        
        # Start animations
        self.animate()
        
        # Run loading tasks in background thread
        threading.Thread(target=self.load_resources, daemon=True).start()
        
        log_debug("Entering LoaderWindow mainloop...")
        self.root.mainloop()
        log_debug("LoaderWindow mainloop ended.")
        
    def animate(self):
        if self.is_done:
            return
            
        self.load_pos += 2
        if self.load_pos > 100:
            self.load_pos = 0
            
        # Update progress bar coords
        x_end = 20 + int(self.load_pos * 2.2) # 220px total width
        self.canvas.coords(self.progress_bar, 20, 85, x_end, 93)
        
        self.root.after(30, self.animate)
        
    def load_resources(self):
        log_debug("Loader background thread started.")
        # 1. Verify Game Exe existence
        if not os.path.exists(os.path.join(base_path, game_exe)):
            log_debug("Game executable PrimeDiablo.exe NOT found!")
            self.canvas.itemconfig(self.status_item, text="ERRO: PrimeDiablo.exe não encontrado", fill="#ff2a2a")
            time.sleep(2.0)
            log_debug("Exiting LoaderWindow due to missing game exe.")
            self.root.after(0, self.root.destroy)
            sys.exit(0)
            
        log_debug("Game executable verified.")
        # 2. Download configurations
        self.canvas.itemconfig(self.status_item, text="Carregando HUB...")
        for name, url in cfgs.items():
            path = os.path.join(base_path, name)
            if not os.path.exists(path):
                download_file(url, path)
                time.sleep(0.1)
                
        # Finish
        log_debug("Loader finished downloading configs. Closing LoaderWindow.")
        self.is_done = True
        time.sleep(0.8)
        self.root.after(0, self.root.destroy)


# ==========================================
# SMART HUD OVERLAY WINDOW
# ==========================================
class OverlayWindow:
    def __init__(self, app):
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("Kakashi Assist Overlay")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#000000")
        self.root.attributes("-alpha", 0.85)
        
        # Position at the top center of the screen
        w, h = 340, 50
        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"{w}x{h}+{(sw - w)//2}+15")
        
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="#050608", highlightthickness=1, highlightbackground="#330000")
        self.canvas.pack(fill="both", expand=True)
        
        # Handle dragging
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        
        # Text fields
        self.hp_text = self.canvas.create_text(15, 15, text="HP: --%", fill="#ff2a2a", font=("Consolas", 10, "bold"), anchor="w")
        self.mp_text = self.canvas.create_text(15, 35, text="MP: --%", fill="#2a8cff", font=("Consolas", 10, "bold"), anchor="w")
        
        self.timer_text = self.canvas.create_text(110, 15, text="RUN: 00:00.0", fill="#ffffff", font=("Consolas", 10, "bold"), anchor="w")
        self.state_text = self.canvas.create_text(110, 35, text="ESTADO: CIDADE", fill="#00ff00", font=("Yu Gothic UI", 9, "bold"), anchor="w")
        
        self.alert_text = self.canvas.create_text(325, 25, text="", fill="#ffea00", font=("Yu Gothic UI", 10, "bold"), anchor="e")
        
        self.locked = False
        self.update_loop()
        
    def start_drag(self, event):
        if not self.locked:
            self._drag_start_x = event.x
            self._drag_start_y = event.y
        
    def do_drag(self, event):
        if not self.locked:
            x = self.root.winfo_x() + event.x - self._drag_start_x
            y = self.root.winfo_y() + event.y - self._drag_start_y
            self.root.geometry(f"+{x}+{y}")
            
    def set_locked(self, lock_state):
        self.locked = lock_state
        hwnd = self.root.winfo_id()
        hwnd = ctypes.windll.user32.GetParent(hwnd)
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        if lock_state:
            style |= 0x00080000 | 0x00000020
            self.canvas.configure(highlightthickness=0, bg="#000000")
            self.root.attributes("-transparentcolor", "#000000")
        else:
            style &= ~(0x00080000 | 0x00000020)
            self.canvas.configure(highlightthickness=1, bg="#050608")
            self.root.attributes("-transparentcolor", "")
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
        
    def update_loop(self):
        if not self.root.winfo_exists():
            return
            
        hp_pct = "--%"
        if self.app.hp_pixel_x > 0 and self.app.hp_pixel_r > 0:
            curr_r, curr_g, _ = get_pixel_color(self.app.hp_pixel_x, self.app.hp_pixel_y)
            if curr_g >= 60:
                hp_pct = "100%"
            elif curr_r < 120 and curr_g < 60:
                val = int((curr_r / self.app.hp_pixel_r) * 100)
                hp_pct = f"{max(0, min(100, val))}%"
            else:
                hp_pct = "100%"
                
        mp_pct = "--%"
        if self.app.mp_pixel_x > 0 and self.app.mp_pixel_b > 0:
            _, _, curr_b = get_pixel_color(self.app.mp_pixel_x, self.app.mp_pixel_y)
            val = int((curr_b / self.app.mp_pixel_b) * 100)
            mp_pct = f"{max(0, min(100, val))}%"
            
        self.canvas.itemconfig(self.hp_text, text=f"HP: {hp_pct}")
        self.canvas.itemconfig(self.mp_text, text=f"MP: {mp_pct}")
        
        if self.app.toolbox_instance and self.app.toolbox_instance.timer_running:
            elapsed = time.time() - self.app.toolbox_instance.timer_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            tenths = int((elapsed * 10) % 10)
            self.canvas.itemconfig(self.timer_text, text=f"RUN: {minutes:02d}:{seconds:02d}.{tenths}")
        else:
            self.canvas.itemconfig(self.timer_text, text="RUN: --:--.-")
            
        self.canvas.itemconfig(self.state_text, text=f"ESTADO: {self.app.game_state}")
        if self.app.game_state == "COMBATE":
            self.canvas.itemconfig(self.state_text, fill="#ff0055")
        elif self.app.game_state == "CIDADE":
            self.canvas.itemconfig(self.state_text, fill="#00ff66")
        elif self.app.game_state == "CARREGANDO":
            self.canvas.itemconfig(self.state_text, fill="#ffcc00")
        else:
            self.canvas.itemconfig(self.state_text, fill="#aaaaaa")
            
        if self.app.active_alerts:
            latest = self.app.active_alerts[-1]
            self.canvas.itemconfig(self.alert_text, text=latest["text"], fill=latest["color"])
        else:
            self.canvas.itemconfig(self.alert_text, text="")
            
        self.root.after(100, self.update_loop)

# ==========================================
# KAKASHI GAMEPLAY TOOLBOX INTERFACE
# ==========================================
class ToolboxWindow:
    def __init__(self, app):
        log_debug("Opening ToolboxWindow...")
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("Kakashi Game Companion Toolbox")
        self.root.geometry("600x560")
        self.root.configure(bg="#0b0c10")
        self.root.attributes("-topmost", app.root.attributes("-topmost"))
        self.root.transient(app.root)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Run Timer variables
        self.timer_running = False
        self.timer_start_time = 0.0
        self.timer_elapsed = 0.0
        self.run_count = 0
        self.run_history = []
        
        # Auto Clicker variables
        self.autoclicker_active = False
        threading.Thread(target=self.autoclicker_loop, daemon=True).start()
        
        # Sidebar Panel (Left Side)
        self.sidebar = tk.Frame(self.root, bg="#050608", width=140, height=560)
        self.sidebar.place(x=0, y=0, width=140, height=560)
        
        # Main Content Frame (Right Side)
        self.content_frame = tk.Frame(self.root, bg="#0b0c10", width=460, height=560)
        self.content_frame.place(x=140, y=0, width=460, height=560)
        
        # Sidebar Title
        tk.Label(
            self.sidebar,
            text="TOOLBOX",
            fg="#ff2a2a",
            bg="#050608",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=15)
        
        # Sidebar Menu Buttons (Modern raise 3D style)
        self.create_sidebar_btn("GUIDES/BUILDS", self.show_builds_tab, 50)
        self.create_sidebar_btn("RUNEWORDS", self.show_runewords_tab, 90)
        self.create_sidebar_btn("BREAKPOINTS", self.show_breakpoints_tab, 130)
        self.create_sidebar_btn("FARM AREAS", self.show_farm_tab, 170)
        self.create_sidebar_btn("RUN TIMER", self.show_timer_tab, 210)
        self.create_sidebar_btn("AUTO CLICKER", self.show_autoclicker_tab, 250)
        self.create_sidebar_btn("SETTINGS", self.show_settings_tab, 290)
        self.create_sidebar_btn("AUTO POT", self.show_autopot_tab, 330)
        
        # Runewords Database
        self.runewords_db = [
            {"name": "Ancient's Pledge", "sockets": "3", "items": "Shield", "runes": "Ral + Ort + Tal", "stats": "+50% Enhanced Defense\nCold Resist +43%\nFire Resist +43%\nLightning Resist +43%\nPoison Resist +43%\n10% Damage Taken Goes To Mana"},
            {"name": "Beast", "sockets": "5", "items": "Axe / Scepter / Hammer", "runes": "Ber + Tir + Um + Mal + Lum", "stats": "Level 9 Fanaticism Aura When Equipped\n+40% Increased Attack Speed\n+240-270% Enhanced Damage\n20% Chance of Crushing Blow\n25% Chance of Open Wounds\nPrevent Monster Heal\n+2 To Werebear\n+2 To Lycanthropy\n40% Increased Attack Speed\nDamage Reduced by 8\n+10 To Energy\n+10 To Strength\nLevel 13 Summon Grizzly (27 Charges)"},
            {"name": "Black", "sockets": "3", "items": "Club / Hammer / Mace", "runes": "Thul + Io + Nef", "stats": "+15% Increased Attack Speed\n+120% Enhanced Damage\n40% Chance of Crushing Blow\nKnockback\nAdds 10-40 Damage\nMagic Damage Reduced By 2\nLevel 4 Corpse Explosion (12 Charges)"},
            {"name": "Brand", "sockets": "4", "items": "Bow / Crossbow", "runes": "Jah + Lo + Mal + Gul", "stats": "35% Chance To Cast Level 14 Amplify Damage When Struck\n100% Chance To Cast Level 18 Bone Spear On Striking\nFires Explosive Arrows or Bolts\n+260-340% Enhanced Damage\nIgnore Target's Defense\n20% Deadly Strike\nPrevent Monster Heal\n20% Bonus To Attack Rating"},
            {"name": "Breath of the Dying", "sockets": "6", "items": "Weapon", "runes": "Vex + Hel + El + Zod + Eth + Tir", "stats": "50% Chance To Cast Level 20 Poison Nova When You Kill An Enemy\nIndestructible\n+60% Increased Attack Speed\n+350-400% Enhanced Damage\nReduce Enemy Defense Per Hit by 25\n+50 To Attack Rating\nHit Causes Monster To Flee 25%\n7% Mana Stolen Per Hit\n12-15% Life Stolen Per Hit\nPrevent Monster Heal\n+30 To All Attributes\n+1 To Light Radius\n+2 Mana After Each Kill"},
            {"name": "Call to Arms (CTA)", "sockets": "5", "items": "Weapon", "runes": "Amn + Ral + Mal + Ist + Ohm", "stats": "+1 To All Skills\n+40% Increased Attack Speed\n+250-290% Enhanced Damage\nAdds 5-30 Fire Damage\n7% Life Stolen Per Hit\n20% Deadly Strike\nPrevent Monster Heal\nLevel 8-12 Battle Command (25 Charges)\nLevel 8-12 Battle Orders (25 Charges)\nLevel 8-12 Battle Cry (25 Charges)\nReplenish Life +12\n30% Better Chance of Getting Magic Items"},
            {"name": "Chains of Honor", "sockets": "4", "items": "Armor", "runes": "Dol + Um + Ber + Ist", "stats": "+2 To All Skills\n+200% Enhanced Defense\nUp to 65% Damage Taken Goes To Mana\nReplenish Life +20\nAll Resistances +65\nDamage Reduced by 8%\n25% Better Chance of Getting Magic Items"},
            {"name": "Chaos", "sockets": "3", "items": "Claw", "runes": "Fal + Ohm + Um", "stats": "9% Chance To Cast Level 11 Frozen Orb On Striking\n11% Chance To Cast Level 9 Charged Bolt On Striking\n+35% Increased Attack Speed\n+290-340% Enhanced Damage\nAdds 216-471 Magic Damage\n25% Chance of Open Wounds\nPrevent Monster Heal\nBonus To Attack Rating +10\n+10 To Strength\nLevel 9 Whirlwind"},
            {"name": "Crescent Moon", "sockets": "3", "items": "Axe / Sword / Polearm", "runes": "Shael + Um + Tir", "stats": "10% Chance To Cast Level 17 Chain Lightning On Striking\n7% Chance To Cast Level 13 Static Field On Striking\n+20% Increased Attack Speed\n+180-220% Enhanced Damage\nIgnore Target's Defense\n-35% To Enemy Lightning Resistance\n25% Chance of Open Wounds\n+9-50 Lightning Damage\n+1-50 Magic Damage\n+2 Mana After Each Kill\nLevel 18 Summon Spirit Wolf (30 Charges)"},
            {"name": "Death", "sockets": "5", "items": "weapon", "runes": "Hel + El + Vex + Ort + Gul", "stats": "100% Chance To Cast Level 44 Chain Lightning When You Die\n25% Chance To Cast Level 18 Glacial Spike On Attack\nIndestructible\n+300-385% Enhanced Damage\n20% Bonus To Attack Rating\n50% Deadly Strike\n20% Increased Attack Speed\nAdds 1-50 Lightning Damage\nRequirements -20%"},
            {"name": "Delirium", "sockets": "3", "items": "Helm", "runes": "Lem + Ist + Io", "stats": "1% Chance To Cast Level 50 Delirium (morph)\n6% Chance To Cast Level 14 Mind Blast When Struck\n14% Chance To Cast Level 13 Terror When Struck\n11% Chance To Cast Level 18 Confuse On Striking\n+2 To All Skills\n+261 Defense\n+10 To Vitality\n50% Extra Gold From Monsters\n25% Better Chance of Getting Magic Items\nLevel 17 Attract (60 Charges)"},
            {"name": "Destruction", "sockets": "5", "items": "Polearm / Sword", "runes": "Vex + Lo + Ber + Jah + Cham", "stats": "23% Chance To Cast Level 12 Volcano On Striking\n5% Chance To Cast Level 23 Molten Boulder On Striking\n100% Chance To Cast Level 45 Meteor When You Die\n15% Chance To Cast Level 22 Nova On Attack\n+350% Enhanced Damage\nIgnore Target's Defense\n20% Deadly Strike\n20% Chance of Crushing Blow\nPrevent Monster Heal\nCannot Be Frozen"},
            {"name": "Doom", "sockets": "5", "items": "Axe / Polearm / Hammer", "runes": "Hel + Ohm + Um + Lo + Cham", "stats": "15% Chance To Cast Level 8 Lower Resist On Striking\nLevel 16 Holy Freeze Aura When Equipped\n+2 To All Skills\n+45% Increased Attack Speed\n+330-370% Enhanced Damage\nReduce Enemy Cold Resist by 15-25%\n20% Deadly Strike\nPrevent Monster Heal\nCannot Be Frozen\nRequirements -20%"},
            {"name": "Dragon", "sockets": "3", "items": "Armor / Shield", "runes": "Sur + Lo + Sol", "stats": "20% Chance To Cast Level 18 Venom When Struck\n12% Chance To Cast Level 15 Hydra On Striking\nLevel 14 Holy Fire Aura When Equipped\n+360 Defense\n+5% To Maximum Mana\n+5% To Maximum Life\nDamage Reduced by 7"},
            {"name": "Dream", "sockets": "3", "items": "Helm / Shield", "runes": "Io + Jah + Pul", "stats": "1-2 To All Skills\n10% Chance To Cast Level 15 Confuse When Struck\nLevel 15 Holy Shock Aura When Equipped\n+20-30% Faster Hit Recovery\n+3.75 (3-37) To Defense (Based on Character Level)\n+10 To Vitality\nAll Resistances +50\n+5-20 To Absorb Lightning Damage"},
            {"name": "Duress", "sockets": "3", "items": "Armor", "runes": "Shael + Um + Thul", "stats": "+40% Faster Hit Recovery\n+10-20% Enhanced Damage\nAdds 37-133 Cold Damage\n15% Chance of Crushing Blow\n33% Chance of Open Wounds\nAll Resistances +15\n20% Faster Block Rate"},
            {"name": "Enigma", "sockets": "3", "items": "Armor", "runes": "Jah + Ith + Ber", "stats": "+2 To All Skills\n+15% Faster Cast Rate\n+1 To Teleport\n+750-775 Defense\nDamage Reduced by 8%\nUp to 14 Life Per Kill (Based on Character Level)\n15% Damage Taken Goes To Mana\n+5% To Maximum Life\n+0.75 To Strength (Based on Character Level)\n+1 Better Chance of Getting Magic Items (Based on Character Level)"},
            {"name": "Exile", "sockets": "4", "items": "Paladin Shield", "runes": "Vex + Ohm + Ist + Dol", "stats": "15% Chance To Cast Level 5 Life Tap On Striking\nLevel 13-16 Defiance Aura When Equipped\n+2 To Offensive Auras (Paladin Only)\n+30% Faster Block Rate\nFreeze Target\nReplenish Life +7\nAll Resistances +50\nDamage Reduced by 7\nEthereal (Indestructible)"},
            {"name": "Faith", "sockets": "4", "items": "Bow / Crossbow", "runes": "Ohm + Jah + Lem + Eld", "stats": "Level 12-15 Fanaticism Aura When Equipped\n+1-2 To All Skills\n+300% Enhanced Damage\nIgnore Target's Defense\n300% Bonus To Attack Rating\n75% Extra Gold From Monsters\n15% Faster Block Rate\nAll Resistances +15"},
            {"name": "Famine", "sockets": "4", "items": "Axe / Hammer", "runes": "Fal + Ohm + Ort + Jah", "stats": "+30% Increased Attack Speed\n+320-370% Enhanced Damage\nAdds 1000 Magic Damage\nAdds 1000 Fire Damage\nAdds 1000 Lightning Damage\nAdds 1000 Cold Damage\nAdds 1000 Poison Damage\nPrevent Monster Heal\n+10 To Strength"},
            {"name": "Fortitude", "sockets": "4", "items": "Weapon / Armor", "runes": "El + Sol + Dol + Lo", "stats": "20% Chance To Cast Level 15 Chilling Armor When Struck\n+25% Faster Cast Rate\n+300% Enhanced Damage\n+200% Enhanced Defense\n+15 Defense\nLife Per Level (1-1.5)\nAll Resistances +25-30\nDamage Reduced by 7\n20% Deadly Strike\nReplenish Life +7\n+1 To Light Radius"},
            {"name": "Gloom", "sockets": "3", "items": "Armor", "runes": "Fal + Um + Pul", "stats": "15% Chance To Cast Level 3 Dim Vision When Struck\n+10% Faster Hit Recovery\n+200-260% Enhanced Defense\n+10 To Strength\nAll Resistances +45\nHalf Freeze Duration\n5% Damage Taken Goes To Mana"},
            {"name": "Grief (Luto)", "sockets": "5", "items": "Sword / Axe", "runes": "Eth + Tir + Lo + Mal + Ral", "stats": "35% Chance To Cast Level 15 Venom On Striking\n+30-40% Increased Attack Speed\nDamage +340-400\nIgnore Target's Defense\n-25% Target Defense\n20% Deadly Strike\nPrevent Monster Heal\nAdds 5-30 Fire Damage\n+2 Mana After Each Kill\nRequirements -20%"},
            {"name": "Hand of Justice", "sockets": "4", "items": "Weapon", "runes": "Sur + Cham + Amn + Lo", "stats": "2 To All Skills\n100% Chance To Cast Level 48 Meteor When You Die\nLevel 16 Holy Fire Aura When Equipped\n+33% Increased Attack Speed\n+280-330% Enhanced Damage\nIgnore Target's Defense\n7% Life Stolen Per Hit\n20% Deadly Strike\nPrevent Monster Heal\nCannot Be Frozen"},
            {"name": "Harmony", "sockets": "4", "items": "Bow / Crossbow", "runes": "Tir + Ith + Sol + Ko", "stats": "Level 10 Vigor Aura When Equipped\n+200-275% Enhanced Damage\nAdds 5-30 Fire Damage\nAdds 5-30 Lightning Damage\nAdds 5-30 Cold Damage\n+2 To Mana After Each Kill\n+9 To Minimum Damage\n+10 To Dexterity\nReplenish Life +20\nLevel 20 Revive (25 Charges)"},
            {"name": "Heart of the Oak (HOTO)", "sockets": "4", "items": "Staff / Mace", "runes": "Ko + Vex + Pul + Thul", "stats": "+3 To All Skills\n+45% Faster Cast Rate\n+75% Damage To Demons\n+100 To Attack Rating Against Demons\nAdds 3-14 Cold Damage\n7% Mana Stolen Per Hit\nReplenish Life +20\n+10 To Dexterity\nAll Resistances +30-40\nLevel 4 Oak Sage (25 Charges)\nLevel 14 Raven (60 Charges)"},
            {"name": "Holy Thunder", "sockets": "4", "items": "Scepter", "runes": "Eth + Ral + Ort + Tal", "stats": "+60% Enhanced Damage\n-25% Target Defense\nAdds 5-30 Fire Damage\nAdds 1-50 Lightning Damage\n+75 Poison Damage Over 5 Seconds\n+10 To Minimum Damage\n+5 To Holy Shock (Paladin Only)\nLevel 7 Chain Lightning (60 Charges)"},
            {"name": "Honor", "sockets": "5", "items": "Weapon", "runes": "Amn + El + Ith + Tir + Sol", "stats": "+1 To All Skills\n+160% Enhanced Damage\n+9 To Minimum Damage\n+9 To Maximum Damage\n7% Life Stolen Per Hit\n+50 To Attack Rating\n+2 Mana After Each Kill\nDamage Reduced By 7\n+1 To Light Radius\nReplenish Life +10"},
            {"name": "Hustle", "sockets": "3", "items": "Weapon / Armor", "runes": "Shael + Ko + Eld", "stats": "+65% Increased Attack Speed\n+40% Faster Run/Walk\n+20% Faster Hit Recovery\n+10 To Dexterity\n7% Chance to Block\nAll Resistances +10\n50% Damage To Undead"},
            {"name": "Ice", "sockets": "4", "items": "Bow / Crossbow", "runes": "Amn + Shael + Jah + Lo", "stats": "100% Chance To Cast Level 40 Blizzard When You Level-Up\n25% Chance To Cast Level 22 Frost Nova On Striking\nLevel 18 Holy Freeze Aura When Equipped\n+20% Increased Attack Speed\n+140-210% Enhanced Damage\nIgnore Target's Defense\n20% Deadly Strike\n7% Life Stolen Per Hit\nReplenish Life +10\nAll Resistances +20"},
            {"name": "Infinity (Infinidade)", "sockets": "4", "items": "Polearm", "runes": "Ber + Mal + Ber + Ist", "stats": "50% Chance To Cast Level 20 Chain Lightning When You Kill An Enemy\nLevel 12 Conviction Aura When Equipped\n+30% Faster Run/Walk\n+255-325% Enhanced Damage\n-45-55% To Enemy Lightning Resistance\n40% Chance of Crushing Blow\nPrevent Monster Heal\n30% Better Chance of Getting Magic Items\n20% Bonus To Attack Rating"},
            {"name": "Insight (Visão)", "sockets": "4", "items": "Polearm / Staff", "runes": "Ral + Tir + Tal + Sol", "stats": "Level 12-17 Meditation Aura When Equipped\n+35% Faster Cast Rate\n+200-260% Enhanced Damage\nAdds 5-30 Fire Damage\nAdds 1-50 Lightning Damage\n+75 Poison Damage Over 5 Seconds\n+9 To Minimum Damage\n+2 Mana After Each Kill\nReplenish Life +7"},
            {"name": "King's Grace", "sockets": "3", "items": "Sword / Scepter / Hammer", "runes": "Amn + Ral + Thul", "stats": "+100% Enhanced Damage\n+100% Damage To Demons\n+100 To Attack Rating Against Demons\nAdds 5-30 Fire Damage\nAdds 3-32 Cold Damage\n7% Life Stolen Per Hit\nReplenish Life +7"},
            {"name": "Last Wish", "sockets": "6", "items": "Sword / Hammer / Axe", "runes": "Jah + Mal + Jah + Sur + Jah + Ber", "stats": "6% Chance To Cast Level 11 Fade When Struck\n10% Chance To Cast Level 18 Venom On Striking\nLevel 17 Might Aura When Equipped\n+330-375% Enhanced Damage\nIgnore Target's Defense\n60-70% Chance of Crushing Blow\nPrevent Monster Heal\nHit Blinds Target\nPrevent Monster Heal\n30% Better Chance of Getting Magic Items"},
            {"name": "Lawbringer", "sockets": "3", "items": "Sword / Hammer / Scepter", "runes": "Amn + Lem + Ko", "stats": "20% Chance To Cast Level 15 Decrepify On Striking\nLevel 16-18 Sanctuary Aura When Equipped\n-50% Target Defense\nAdds 150-210 Fire Damage\nAdds 130-180 Cold Damage\n7% Life Stolen Per Hit\n75% Extra Gold From Monsters\n+10 To Dexterity\nSlain Monsters Rest In Peace"},
            {"name": "Lionheart", "sockets": "3", "items": "Armor", "runes": "Hel + Lum + Fal", "stats": "+20% Enhanced Damage\n+25 To Strength\n+15 To Dexterity\n+20 To Vitality\n+10 To Energy\n+50 To Life\nAll Resistances +30\nRequirements -15%"},
            {"name": "Lore (Sabedoria)", "sockets": "2", "items": "Helm", "runes": "Ort + Sol", "stats": "+1 To All Skills\n+10 To Energy\nLightning Resist +30%\nDamage Reduced By 7\n+2 To Mana After Each Kill\n+2 To Light Radius"},
            {"name": "Malice", "sockets": "3", "items": "Melee Weapon", "runes": "Ith + El + Eth", "stats": "+33% Enhanced Damage\n+9 To Minimum Damage\nPrevent Monster Heal\n-25% Target Defense\n100% Chance of Open Wounds\nDrain Life -5"},
            {"name": "Melody", "sockets": "3", "items": "Bow / Crossbow", "runes": "Shael + Ko + Nef", "stats": "+3 To Bow and Crossbow Skills (Amazon Only)\n+20% Increased Attack Speed\n+50% Enhanced Damage\n+300% Damage To Undead\nKnockback\n+10 To Dexterity\n20% Faster Hit Recovery\nLevel 6 Slow Missiles (10 Charges)\nLevel 3 Fade (30 Charges)"},
            {"name": "Memory", "sockets": "4", "items": "Staff", "runes": "Lum + Io + Sol + Eth", "stats": "+3 To Sorceress Skill Levels\n+33% Faster Cast Rate\n+20% Faster Hit Recovery\n+10 To Energy\n+10 To Vitality\n+9 To Minimum Damage\nMagic Damage Reduced By 7\nRequirements -20%"},
            {"name": "Nadir", "sockets": "2", "items": "Helm", "runes": "Nef + Tir", "stats": "+50% Enhanced Defense\n+30 Defense Vs. Missile\n+10 To Energy\nPoison Resist +50%\n+2 Mana After Each Kill\n+2 To Light Radius\nLevel 13 Cloak of Shadows (3 Charges)"},
            {"name": "Oath", "sockets": "4", "items": "Sword / Axe / Mace", "runes": "Shael + Pul + Mal + Lum", "stats": "30% Chance To Cast Level 20 Bone Spirit On Striking\nIndestructible\n+50% Increased Attack Speed\n+210-340% Enhanced Damage\n75% Damage To Demons\nPrevent Monster Heal\n+10 To Energy\n20% Faster Hit Recovery\nAll Resistances +20"},
            {"name": "Obedience", "sockets": "5", "items": "Polearm", "runes": "Hel + Ko + Thul + Eth + Fal", "stats": "30% Chance To Cast Level 21 Enchant When You Kill An Enemy\n+40% Faster Hit Recovery\n+370% Enhanced Damage\n-25% Target Defense\nAdds 3-32 Cold Damage\nLightning Resist +30%\n+10 To Dexterity\n+10 To Strength\nRequirements -20%"},
            {"name": "Passion", "sockets": "4", "items": "Weapon", "runes": "Dol + Ort + Pul + Lem", "stats": "25% Chance To Cast Level 3 Heart of Wolverine On Striking\n+25% Increased Attack Speed\n+160-210% Enhanced Damage\nAdds 1-50 Lightning Damage\nHit Causes Monster To Flee 25%\n75% Extra Gold From Monsters\nLevel 3 Berserk (12 Charges)\nLevel 3 Zeal (12 Charges)"},
            {"name": "Peace", "sockets": "3", "items": "Armor", "runes": "Shael + Thul + Amn", "stats": "4% Chance To Cast Level 5 Slow Missiles When Struck\n2% Chance To Cast Level 15 Valkyrie On Striking\n+2 To Amazon Skill Levels\n+20% Faster Hit Recovery\nAdds 3-32 Cold Damage\n7% Life Stolen Per Hit\nAll Resistances +10"},
            {"name": "Phoenix", "sockets": "4", "items": "Weapon / Shield", "runes": "Vex + Vex + Lo + Jah", "stats": "40% Chance To Cast Level 22 Firestorm On Striking\nLevel 13 Redemption Aura When Equipped\n+350-400% Enhanced Damage\nIgnore Target's Defense\n14% Mana Stolen Per Hit\n20% Deadly Strike\n+5% To Maximum Fire Resist\nRequirements -20%"},
            {"name": "Pride", "sockets": "4", "items": "Polearm", "runes": "Cham + Sur + Io + Lo", "stats": "25% Chance To Cast Level 17 Fire Wall When Struck\nLevel 15 Concentration Aura When Equipped\n+260-300% Enhanced Damage\nIgnore Target's Defense\n20% Deadly Strike\nHit Blinds Target\nFreezes Target +3\n+10 To Vitality\nReplenish Life +8"},
            {"name": "Principle", "sockets": "3", "items": "Armor", "runes": "Ral + Gul + Eld", "stats": "100% Chance To Cast Level 5 Holy Bolt On Striking\n+2 To All Skills\n+30% Faster Run/Walk\nPoison Resist +50%\nFire Resist +30%\nMagic Damage Reduced By 7\n15% Damage Taken Goes To Mana"},
            {"name": "Prudence", "sockets": "2", "items": "Armor", "runes": "Mal + Tir", "stats": "+25% Faster Hit Recovery\n+140-170% Enhanced Defense\nAll Resistances +25-35\nDamage Reduced By 3\nMagic Damage Reduced By 3\n+2 Mana After Each Kill\nReplenish Life +4\nIndestructible"},
            {"name": "Radiance", "sockets": "3", "items": "Helm", "runes": "Nef + Sol + Ith", "stats": "+75% Enhanced Defense\n+30 Defense Vs. Missile\n+10 To Energy\nDamage Reduced By 7\nMagic Damage Reduced By 3\n15% Damage Taken Goes To Mana\n+2 To Light Radius\nReplenish Life +7"},
            {"name": "Rain", "sockets": "3", "items": "Staff", "runes": "Ort + Mal + Ith", "stats": "5% Chance To Cast Level 15 Cyclone Armor When Struck\n5% Chance To Cast Level 15 Twister On Striking\n+2 To Druid Skill Levels\n+20% Faster Cast Rate\nAdds 1-50 Lightning Damage\nMagic Damage Reduced By 7\n15% Damage Taken Goes To Mana"},
            {"name": "Rhyme", "sockets": "2", "items": "Shield", "runes": "Shael + Eth", "stats": "+20% Faster Block Rate\n20% Increased Chance of Blocking\nAll Resistances +25\nRegenerate Mana 15%\nCannot Be Frozen\n50% Extra Gold From Monsters\n25% Better Chance of Getting Magic Items"},
            {"name": "Rift", "sockets": "4", "items": "Polearm / Scepter", "runes": "Hel + Ko + Lem + Gul", "stats": "20% Chance To Cast Level 16 Tornado On Striking\n16% Chance To Cast Level 21 Frozen Orb On Attack\n20% Bonus To Attack Rating\n75% Extra Gold From Monsters\n+10 To Dexterity\nRequirements -20%\nLevel 15 Iron Maiden (40 Charges)"},
            {"name": "Silence", "sockets": "6", "items": "Weapon", "runes": "Dol + Eld + Hel + Ist + Tir + Vex", "stats": "+2 To All Skills\n+20% Increased Attack Speed\n+75% Damage To Undead\nHit Causes Monster To Flee 25%\nPrevent Monster Heal\n7% Mana Stolen Per Hit\nAll Resistances +75\n30% Better Chance of Getting Magic Items\nRequirements -20%"},
            {"name": "Smoke", "sockets": "2", "items": "Armor", "runes": "Nef + Lum", "stats": "20% Chance To Cast Level 1 Fade When Struck\n+75-100% Enhanced Defense\n+30 Defense Vs. Missile\nAll Resistances +50\n+10 To Energy\n20% Faster Hit Recovery\nLevel 6 Cloak of Shadows (18 Charges)"},
            {"name": "Spirit (Espírito)", "sockets": "4", "items": "Sword / Shield", "runes": "Tal + Thul + Ort + Amn", "stats": "+2 To All Skills\n+25-35% Faster Cast Rate\n+55% Faster Hit Recovery\nAdds 1-50 Lightning Damage\nAdds 3-32 Cold Damage\n+75 Poison Damage Over 5 Seconds\n7% Life Stolen Per Hit\nAll Resistances +35\n+8 To Mana After Each Kill\n+22 To Vitality"},
            {"name": "Splendor", "sockets": "2", "items": "Shield", "runes": "Eth + Lum", "stats": "+1 To All Skills\n+10% Faster Cast Rate\n+20% Faster Block Rate\n+60-100% Enhanced Defense\nRegenerate Mana 15%\n+10 To Energy\n50% Extra Gold From Monsters\n20% Better Chance of Getting Magic Items\n+3 To Light Radius"},
            {"name": "Stealth (Furtividade)", "sockets": "2", "items": "Armor", "runes": "Tal + Eth", "stats": "Magic Damage Reduced By 3\n+6 To Dexterity\nRegenerate Mana 15%\n+75 Poison Damage Over 5 Seconds\nPoison Resist +30%\n25% Faster Run/Walk\n25% Faster Cast Rate\n25% Faster Hit Recovery"},
            {"name": "Stone", "sockets": "4", "items": "Armor", "runes": "Shael + Um + Pul + Lum", "stats": "+40% Faster Hit Recovery\n+250-290% Enhanced Defense\n+300 Defense Vs. Missile\n+10 To Energy\nAll Resistances +15\nLevel 16 Clay Golem (16 Charges)\nLevel 16 Molten Boulder (80 Charges)"},
            {"name": "Treachery", "sockets": "3", "items": "Armor", "runes": "Shael + Thul + Lem", "stats": "5% Chance To Cast Level 15 Fade When Struck\n25% Chance To Cast Level 15 Venom On Striking\n+2 To Assassin Skill Levels\n+45% Increased Attack Speed\n+20% Faster Hit Recovery\nCold Resist +30%\n50% Extra Gold From Monsters"},
            {"name": "Venom", "sockets": "3", "items": "Weapon", "runes": "Tal + Dol + Mal", "stats": "Ignore Target's Defense\nPrevent Monster Heal\nHit Causes Monster To Flee 25%\n+273 Poison Damage Over 6 Seconds\nLevel 15 Poison Nova (15 Charges)"},
            {"name": "Wealth", "sockets": "3", "items": "Armor", "runes": "Lem + Ko + Tir", "stats": "+10 To Dexterity\n+2 Mana After Each Kill\n300% Extra Gold From Monsters\n100% Better Chance of Getting Magic Items"},
            {"name": "White", "sockets": "2", "items": "Necromancer Wand / Necromancer Dagger", "runes": "Dol + Io", "stats": "+3 To Poison and Bone Skills (Necromancer Only)\n+20% Faster Cast Rate\n+30% Faster Hit Recovery\nHit Causes Monster To Flee 25%\n+10 To Vitality\nMagic Damage Reduced By 4\nLevel 4 Bone Armor (12 Charges)"},
            {"name": "Zephyr", "sockets": "2", "items": "Bow / Crossbow", "runes": "Ort + Eth", "stats": "20% Faster Run/Walk\n+25% Increased Attack Speed\n+33% Enhanced Damage\nAdds 1-50 Lightning Damage\n-25% Target Defense\nDefense +25\nRequirements -10%"},
            {"name": "Edge", "sockets": "3", "items": "Bow / Crossbow", "runes": "Tir + Tal + Amn", "stats": "Level 15 Thorns Aura When Equipped\n+30% Increased Attack Speed\n+260-300% Damage To Demons\nPrevent Monster Heal\n7% Life Stolen Per Hit\n+2 Mana After Each Kill\nReduces All Vendor Prices 15%"},
            {"name": "Bramble", "sockets": "4", "items": "Armor", "runes": "Ral + Ohm + Sur + Eth", "stats": "Level 15-21 Thorns Aura When Equipped\n+50% Faster Hit Recovery\n+300% Enhanced Defense\n+5% To Maximum Cold Resist\nIncrease Maximum Mana 5%\nRegenerate Mana 15%\n+30% To Poison Skill Damage"},
            {"name": "Mist", "sockets": "5", "items": "Bow / Crossbow", "runes": "Cham + Shael + Gul + Thul + Ith", "stats": "Level 8-12 Concentration Aura When Equipped\n+3 To All Skills\n+20% Increased Attack Speed\n+100% Piercing Attack\n+325-375% Enhanced Damage\nAdds 3-32 Cold Damage\nCannot Be Frozen\n25% Better Chance of Getting Magic Items"},
            {"name": "Plague", "sockets": "3", "items": "Weapon", "runes": "Fal + Um + Pul", "stats": "20% Chance To Cast Level 12 Lower Resist On Striking\n25% Chance To Cast Level 15 Poison Nova On Attack\n+275-325% Enhanced Damage\nIgnore Target's Defense\nAll Resistances +20-30\nRequirements -20%"},
            {"name": "Unbending Will", "sockets": "5", "items": "Sword", "runes": "Fal + Io + Eth + Lum + Ko", "stats": "18% Chance To Cast Level 8 Blade Fury On Striking\n+3 To All Skills\n+300-350% Enhanced Damage\nIgnore Target's Defense\n20% Increased Attack Speed\nPrevent Monster Heal\n+10 To Strength\n+10 To Vitality\n+10 To Energy\n+10 To Dexterity\nAll Resistances +20"},
            {"name": "Wisdom", "sockets": "3", "items": "Helm", "runes": "Pul + Ith + Eld", "stats": "+15-25% Faster Cast Rate\nIncrease Maximum Mana 5%\nRegenerate Mana 15%\n33% Piercing Attack\n+15 Defense\nLightning Resist +33%\n75% Damage To Undead\n+10 To Energy"},
            {"name": "Wrath", "sockets": "4", "items": "Weapon", "runes": "Pul + Lum + Ber + Mal", "stats": "30% Chance To Cast Level 1 Decrepify On Striking\n5% Chance To Cast Level 18 Life Tap On Striking\n+250-300% Enhanced Damage\nAdds 60-120 Magic Damage\nAdds 10-40 Lightning Damage\n20% Chance of Crushing Blow\nPrevent Monster Heal\nAll Resistances +20\n20% Bonus To Attack Rating"},
            {"name": "Frost Soul", "sockets": "2", "items": "Staff / Orb", "runes": "Tir + Thul", "stats": "+2 To Cold Skills (Sorceress Only)\n+20% Enhanced Defense\n+3 To Frost Nova (Sorceress Only)\n+3 To Ice Blast (Sorceress Only)\n+3 To Glacial Spike (Sorceress Only)\n+10 To All Resistances\n+2 Mana After Each Kill\nAdds 3-32 Cold Damage (Cold Length 3 seconds)"},
            {"name": "Zakarum's Star", "sockets": "5", "items": "Sword / Scepter", "runes": "Sur + Jah + Ko + Mal + Lo", "stats": "Level 12-16 Holy Shock Aura When Equipped\n+30% Increased Attack Speed\n+300 To Attack Rating\n+270-320% Enhanced Damage\n-45-55% To Enemy Lightning Resistance\n-50% Target Defense\nHit Blinds Target\nIgnore Target's Defense\n+10 To Dexterity\nPrevent Monster Heal\n20% Deadly Strike"},
            {"name": "Charged Javelin", "sockets": "3", "items": "Javelin", "runes": "Ort + Amn + Fal", "stats": "+1-2 Javelins & Spears Skills (Amazon)\n30% Increased Attack Speed\n+3 to Charged Strike\n150-250% Enhanced Damage\n+5 to Mana After Each Kill\n10% Chance to Cast Level 15 Nova on Striking\n+1-50 Lightning Damage\n7% Life Stolen Per Hit\n+10 to Strength"},
            {"name": "Venomous Nature", "sockets": "4", "items": "Armor", "runes": "Gul + Ber + Jah + Cham", "stats": "+2 to All Skills\n+2 to Shape Shifting Skills\n+25% Faster Hit Recovery\n+35-45% to Poison Skill Damage\n+1 to Teleport\n170-250% Enhanced Defense\n+5 to Maximum Poison Resist\nDamage Reduced by 8%\n+5% Increased Maximum Life\nCannot Be Frozen"},
            {"name": "Pillar's of Zakarum", "sockets": "5", "items": "Sword / Axe", "runes": "Zod + Lo + Shael + Mal + Lo", "stats": "Level 12 Fanaticism Aura When Equipped\n+2 to Paladin Skill Levels\n+350-400% Enhanced Damage\n-35-50% to Enemy Fire Resistance\n-35-50% to Enemy Lightning Resistance\n-35-50% to Enemy Cold Resistance\nIndestructible\n+20% Deadly Strike\n+20% Increased Attack Speed\nPrevent Monster Heal\n+20% Deadly Strike"},
            {"name": "Time Lock", "sockets": "3", "items": "Helm / Shield", "runes": "Ist + Lo + Ohm", "stats": "Level 7-8 Holy Freeze Aura When Equipped\n+2 to All Skills\n+0.38 Dexterity per Level\n+20% Faster Hit Recovery\n170-220% Enhanced Defense\n+20 to All Resistances\n+25% Better Chance of Getting Magic Items\n+5% to Maximum Lightning Resist\n+5% to Maximum Cold Resist"},
            {"name": "Robin Hood", "sockets": "3", "items": "Bow / Crossbow", "runes": "Tir + Nef + Amn", "stats": "5% Chance to Cast Level 14 Burst of Speed When You Kill an Enemy\n+3 to Bow and Crossbow Skills\n+200% Enhanced Damage\n+3 to Magic Arrow (Amazon Only)\n+100% Extra Gold from Monsters\n+100% Magic Find\n+2 Mana Per Kill\nKnockback\n7% Life Stolen Per Hit"},
            {"name": "Flickering Flame", "sockets": "3", "items": "Helm", "runes": "Nef + Pul + Vex", "stats": "Level 4-8 Resist Fire Aura When Equipped\n+3 to Fire Skills\n-10-15% Enemy Fire Resistance\n+50-75 Mana\nHalf Freeze Duration\nPoison Length Reduced by 50%\n+30 Defense vs Missile\n+30% Enhanced Defense\n+5% to Maximum Fire Resist"},
            {"name": "Massive", "sockets": "3", "items": "Sword / Axe / Mace / Claw", "runes": "El + Tir + Eth", "stats": "Level 3 Might Aura When Equipped\n+20% Increased Attack Speed\n30% Faster Run/Walk\n+150% Enhanced Damage\nCannot Be Frozen\n+0.625 Strength per Level\n+50 to Attack Rating\n+2 Mana Per Kill\n-25% Target Defense"},
            {"name": "Leaf (Folha)", "sockets": "2", "items": "Staff / Orb", "runes": "Tir + Ral", "stats": "+2 to Fire Skills\n20% Enhanced Defense\n+3 to Fireburst (Sorceress Only)\n+3 to Firewall (Sorceress Only)\n+3 to Enchant (Sorceress Only)\n+10 to All Resistances\n+2 Mana Per Kill\n+5-30 Fire Damage"},
            {"name": "Offering", "sockets": "3", "items": "Helm / Shield", "runes": "Ith + Um + Vex", "stats": "+10% Chance to Cast Level 6 Life Tap on Striking\nLevel 15 Sanctuary Aura When Equipped\n+3 to Sacrifice (Paladin Only)\n+100 Defense vs Missile\n+110-190% Enhanced Damage\n+20% Increased Attack Speed\n7% Life Stolen Per Hit\n+10 to Vitality\n7% Life Stolen Per Hit"},
            {"name": "Achilles Spear", "sockets": "3", "items": "Javelin / Spear / Polearm", "runes": "Vex + Shael + Ber", "stats": "+3 to Javelin & Spear Skills (Amazon Only)\nLevel 13-18 Fanaticism Aura When Equipped\n+3 to Fend\n+3 to Jab\n290-370% Enhanced Damage\n15% Chance to Cast Level 6 Amplify Damage on Striking\n7% Mana Stolen Per Hit\n+20% Increased Attack Speed\n+20% Chance Of Crushing Blow"},
            {"name": "Storm", "sockets": "2", "items": "Staff / Orb", "runes": "Tir + Ort", "stats": "+2 to Lightning Skills\n20% Enhanced Defense\n+3 to Nova (Sorceress Only)\n+3 to Chain Lightning (Sorceress Only)\n+3 to Thunderstorm (Sorceress Only)\n+10 to All Resistances\n+2 Mana Per Kill\n+1-50 Lightning Damage"},
            {"name": "Overdrive", "sockets": "3", "items": "Weapon", "runes": "Hel + Shael + Hel", "stats": "Level 3 Fanaticism Aura When Equipped\nPiercing Attack +20%\n+130-170% Enhanced Damage\n+20-30% Crushing Blow\n+33% Deadly Strike\n+0.625 Dexterity per Level\n-20% Requirements\n+20% Increased Attack Speed\n-20% Requirements"},
            {"name": "Swiftblade", "sockets": "3", "items": "Sword / Axe / Mace / Claw", "runes": "Ort + Shael + Sol", "stats": "15% Chance to Cast Level 8 Nova on Striking\n10% Chance to Cast Level 10 Chain Lightning on Kill\n+2 to Martial Arts (Assassin Only)\n7% Life Stolen Per Hit\n+150-200% Enhanced Damage\n+3 to Claws of Thunder\n+1-50 to Lightning Damage\n+20% Increased Attack Speed\n+9 to Minimum Damage"},
            {"name": "Warbringer", "sockets": "6", "items": "Weapon", "runes": "Ber + Lo + Jah + Mal + Hel + Zod", "stats": "Level 12 Heart of Wolverine Aura When Equipped\n+500 to Attack Rating\n+50% Increased Attack Speed\n+450% Enhanced Damage\n+30% Deadly Strike\nDamage Reduced by 10%\n20% Crushing Blow\n20% Deadly Strike\nIgnore Target's Defense\nPrevent Monster Heal\n-20% Requirements\nIndestructible"},
            {"name": "Eternity", "sockets": "3", "items": "Staff / Orb", "runes": "Lum + Jah + Mal", "stats": "+3 to All Skills\n+40% Faster Cast Rate\n+0.625 Dexterity per Level\n+30-40% Cold Skill Damage\n+47-147 Mana\n+5-20 All Resistances\n+10 Energy\nIgnores Target Defense\nPrevent Monster Heal"},
            {"name": "Viper", "sockets": "3", "items": "Shield", "runes": "Nef + Gul + Eth", "stats": "+1 to All Skills\n30% Increased Attack Speed\n20% Crushing Blow\n+500 Poison Damage over 1 second\n+0.375 Dexterity per Level\n+15 All Resistances\n+30 Defense vs Missile\nRegenerate Mana 15%\n+5 to Max Poison Resist"},
            {"name": "Doomsayer", "sockets": "3", "items": "Shield", "runes": "Um + Jah + Lo", "stats": "+1 to All Skills\nLevel 4-7 Concentration Aura When Equipped\n15% Chance to Cast Level 44 War Cry on Striking\n30% Increased Attack Speed\n+150-200% Enhanced Damage\n+20% Crushing Blow\n+15 All Resistances\n+5% Maximum Lightning Resist"},
            {"name": "Spellshot", "sockets": "2", "items": "Arrows / Bolts", "runes": "Ber + Ko", "stats": "+1 to All Skills\n+20% Increased Attack Speed\n15% Piercing Attack\n-10-20% Enemy Fire Resistance\n-10-20% Enemy Cold Resistance\n80% Magic Find\nDamage Reduced by 8%\n+10 Dexterity"},
            {"name": "Midas' Touch", "sockets": "2", "items": "Armor / Helm / Shield / Weapon", "runes": "Lem + Lum", "stats": "+1 to All Skills\n10% Chance to Cast Level 10 Terror When Struck\n+50 Life\n+20 All Resistances\n+80% Magic Find\n-20% Requirements\n+75% Extra Gold from Monsters\n+50% Extra Gold from Monsters\n+10 Energy\n+10 Energy"},
            {"name": "Desolation", "sockets": "3", "items": "Staff / Orb", "runes": "Jah + Lum + Mal", "stats": "+3 to All Skills\n+40% Faster Cast Rate\n+0.625 Dexterity per Level\n-30-40% Enemy Fire Resistance\n+47-147 Mana\n+5-20 All Resistances\n+10 Energy\nIgnores Target Defense\nPrevent Monster Heal"},
            {"name": "Blink", "sockets": "3", "items": "Armor", "runes": "Um + Ber + Ist", "stats": "+1 to All Skills\n+20% Faster Cast Rate\n+150% Enhanced Defense\n+1 to Teleport\n-20% Requirements\n+20 Strength\n+15 All Resistances\nDamage Reduced by 8%\n+25% Magic Find"},
            {"name": "Predator", "sockets": "3", "items": "Helm", "runes": "Cham + Ber + Hel", "stats": "12% Chance to Cast Level 6 Amplify Damage on Striking\n+30% Increased Attack Speed\n+100-150% Enhanced Damage\n+200% Enhanced Defense\n+1 to Critical Strike\n+15 Life After Each Kill\nCannot Be Frozen\nDamage Reduced by 8%\n-15% Requirements"},
            {"name": "Or Kadma'ah", "sockets": "3", "items": "Staff / Orb", "runes": "Mal + Jah + Lum", "stats": "+3 to All Skills\n+40% Faster Cast Rate\n+0.625 Dexterity per Level\n-30-40% Enemy Lightning Resistance\n+47-147 Mana\n+5-20 All Resistances\n+10 Energy\nIgnores Target Defense\nPrevent Monster Heal"},
            {"name": "Haze", "sockets": "3", "items": "Armor", "runes": "Yo + Um + Pul", "stats": "5% Chance to Cast Level 10 Confuse When Struck\n+30% Faster Cast Rate\n+30% Faster Hit Recovery\n+750-775 Defense\n+30 All Resistances\n20% Damage Taken Goes to Mana\n+10 Vitality\n+15 All Resistances\n+30% Defense"},
            {"name": "Coup de Grâce", "sockets": "3", "items": "Claw", "runes": "Lo + Jah + Gul", "stats": "+2 to All Skills\n+20% Faster Cast Rate\n+30% Increased Attack Speed\n+40% Open Wounds\n+7-10 to Whirlwind\n+0.625 Dexterity per Level\n+20% Deadly Strike\nIgnores Target Defense\n+20% Attack Rating"},
            {"name": "Hermes' Pace", "sockets": "4", "items": "Armor / Shield", "runes": "Sur + Um + Jah + Shael", "stats": "+1 to All Skills\n+30% Faster Cast Rate\n+30% Faster Hit Recovery\n+220-320% Enhanced Defense\n+1 to Teleport\n+0.75 Dexterity per Level\n+400 Defense vs Missile\n+5% Increased Maximum Mana\n+15 All Resistances\n+5% Increased Maximum Life\n+20% Faster Hit Recovery / +20% Faster Block Rate"},
            {"name": "Maestro", "sockets": "5", "items": "Weapon", "runes": "Um + Gul + Eth + Mal + Ist", "stats": "Level 8-10 Might Aura When Equipped\n50% Increased Attack Speed\n180% Enhanced Damage\n10% Life Stolen per Hit\n20% Crushing Blow\n250 Magic Damage\n25% Chance to Open Wounds\n+20% Attack Rating\n-25% Target Defense\nPrevent Monster Heal\n30% Magic Find"},
            {"name": "Electric Spire", "sockets": "3", "items": "Claw / Amazon Item", "runes": "Vex + Lo + Amn", "stats": "+1 to All Skills\nLevel 14 Holy Shock When Equipped\n15% Chance to Cast Level 34 Nova On Striking\n20% Increased Attack Speed\n200-250% Enhanced Damage\n-20% Enemy Lightning Resistance\n7% Mana Stolen per Hit\n+20% Deadly Strike\n7% Life Stolen per Hit"},
            {"name": "Mantra", "sockets": "2", "items": "Shield", "runes": "Um + Pul", "stats": "+1 to All Skills\nLevel 3 Meditation Aura When Equipped\n+20% Faster Cast Rate\n56% Faster Block Rate\n30% Chance of Blocking\nDamage Reduced by 15%\n+22% All Resistances\n+30% Enhanced Defense"},
            {"name": "Spartan", "sockets": "3", "items": "Helm", "runes": "Um + Ith + Nef", "stats": "Piercing Attack 40%\n4-8% Life Stolen per Hit\n20% Faster Hit Recovery\n+50-100% Enhanced Damage\n+50-100% Enhanced Defense\n+30 Dexterity\n+15 All Resistances\n15% Damage Taken Goes to Mana\n+30 Defense vs Missile"},
            {"name": "Hellbane", "sockets": "3", "items": "weapon", "runes": "Amn + Gul + Lo", "stats": "20% Chance to Cast Level 6 Lower Resist\nLevel 3-4 Conviction Aura When Equipped\n+30% Increased Attack Speed\n+2 to Life (per Level)\n+200% Damage to Demons\n+270-320% Enhanced Damage\n7% Life Stolen per Hit\nPrevent Monster Heal\n+20% to Attack Rating\n+20% Deadly Strike"},
            {"name": "EVIL", "sockets": "2", "items": "Class Items / Helm", "runes": "Um + Mal", "stats": "+2 to All Skills\n20% Increased Attack Speed\n150% Enhanced Damage\nDamage Reduced by 10%\nSlain Monsters Rest in Peace\n+10 Life After Each Kill\n+10 Mana After Each Kill\n25% Open Wounds\n+15% All Resistances\n+22% All Resistances\nPrevent Monster Heal\nMagic Damage Reduced by 7"},
            {"name": "FIBONNACI", "sockets": "2", "items": "Class Items", "runes": "Um + Ohm", "stats": "+3 to All Skills\n20% Faster Cast Rate\n1-3 To Conviction\nSlain Monsters Rest in Peace\n+10 Life After Each Kill\n+10 Mana After Each Kill\n25% Open Wounds\n+15% All Resistances\n+22% All Resistances\n50% Enhanced Damage\n+5% to Maximum Cold Resist"},
            {"name": "PUZZLE", "sockets": "2", "items": "Class Items", "runes": "Shael + Vex", "stats": "+2 to All Skills\n10% Faster Hit Recovery\n10% Chance to Block\n10% Maximum Life\n12% Faster Block Rate\n+20 to All Resistances\n+20% Faster Cast Rate\n20% Increased Attack Speed\n20% Faster Hit Recovery\n20% Faster Block Rate\n7% Mana Stolen per Hit\n+5% to Maximum Fire Resist"},
            {"name": "INARIUS' COVET", "sockets": "3", "items": "Polearm / Missile Weapon", "runes": "Zod + Jah + Lo", "stats": "+3 to All Skills\n+30% Faster Cast Rate\n40% Increased Attack Speed\n5% Chance to Cast Level 12 Fade When Struck\nLevel 20 Conviction Aura When Equipped\n+300-450% Enhanced Damage\nSlows Target by 20%\nIndestructible\nIgnores Target Defense\n20% Deadly Strike"},
            {"name": "PILLARS OF CREATION", "sockets": "3", "items": "Shield", "runes": "Lo + Jah + Zod", "stats": "+2 to All Skills\n+56% Faster Block Rate\n+30% Chance to Block\n+250-320% Enhanced Defense\n+10-20 to All Attributes\n+70 to All Resistances\nDamage Reduced by 25%\n+5% to Maximum Lightning Resist\n+50 to Life\nIndestructible"},
            {"name": "SKELETON KING", "sockets": "2", "items": "Helm / Shield", "runes": "Sur + Lo", "stats": "+2 to All Skills\n20% Faster Hit Recovery\n1-3 to Summon Resist\n6-10 to Raise Skeleton\n6-10 to Raise Skeletal Mage\n10-15 to Skeleton Mastery\n15-30 to All Resistances\n+5% to Maximum Mana\n+50 to Mana\n+5% to Maximum Lightning Resist"},
            {"name": "WOLF PACK", "sockets": "2", "items": "Helm / Shield", "runes": "Um + Ber", "stats": "+2 to All Skills\n20% Faster Hit Recovery\n8-12 to Summon Spirit Wolf\n8 to Solar Creeper\n6-10 to Summon Dire Wolf\n6-10 to Summon Grizzly\nCannot Be Frozen\n+15% to All Resistances\n+22% to All Resistances\nDamage Reduced by 8%"},
            {"name": "BELIAL'S DECEIT", "sockets": "3", "items": "Helm", "runes": "Um + Ber + Um", "stats": "20% Chance to Cast Level 16 Corpse Explosion On Attack\n-20% Increased Attack Speed\n-20% Faster Cast Rate\n150-200% Enhanced Defense\n+10 to All Attributes\nIncrease Maximum Life 10-15%\n10% to Maximum All Resists\n+15% to All Resistances\nDamage Reduced by 8%\n+15% to All Resistances"},
            {"name": "ANDARIEL'S CARESS", "sockets": "3", "items": "Weapon", "runes": "Zod + Ber + Jah", "stats": "+2-3 to All Skills\n12% Chance to Cast Level 10 Lower Resist on Striking\n75% Increased Attack Speed\n+350-450% Enhanced Damage\n-30-40% to Enemy Poison Resistance\nPrevent Monster Heal\n33% Open Wounds\nIndestructible\n20% Crushing Blow\nIgnores Target Defense"},
            {"name": "AZMODAN'S AVARICE", "sockets": "4", "items": "Armor", "runes": "Lem + Lo + Vex + Vex", "stats": "+1 to All Skills\n+1 to Teleport\n15% Chance to Cast Level 30 Firestorm on Striking\n+1.725 to Energy (per Level)\n+1.725 to Vitality (per Level)\n75-150% Magic Find\n-15% Vendor Price\n+50% Extra Gold From Monsters\n+5% to Maximum Lightning Resist\n+5% to Maximum Fire Resist\n+5% to Maximum Fire Resist"},
            {"name": "DURIEL'S HUNGER", "sockets": "4", "items": "Armor", "runes": "Cham + Dol + Um + Ber", "stats": "+2 to All Skills\n+1 to Teleport\n+200-300% Enhanced Defense\nLevel 10-14 Holy Freeze Aura When Equipped\n15-20% Life Stolen per Hit\n45% Crushing Blow\nReplenish Life +30\nCannot Be Frozen\nReplenish Life +7\n+15% to All Resistances\nDamage Reduced by 8%"},
            {"name": "WRATH OF MEPHISTO", "sockets": "3", "items": "Helm", "runes": "Ohm + Ber + Lo", "stats": "+1-2 to All Skills\nLevel 8 Conviction Aura When Equipped\n20% Increased Attack Speed\n+200-300% Enhanced Defense\n20% Chance to Cast Level 57 Charged Bolt on Striking\nAdds 1-1150 Lightning Damage\n-7-15% to Enemy Lightning Resistance\n+5% to Maximum Cold Resist\nDamage Reduced by 8%\n+5% to Maximum Lightning Resist"},
            {"name": "IMPERIUS' PRIDE", "sockets": "5", "items": "Armor", "runes": "Zod + Jewel + Jah + Jewel + Cham", "stats": "+3 to All Skills\n+20% Chance to Block\n+1 to Teleport\n+20% Faster Cast Rate\n+100-150% Enhanced Damage\n+200% Enhanced Defense\nDamage Reduced by 10-15%\nIndestructible\n+5% to Maximum Life\nCannot Be Frozen"},
            {"name": "Albatroz", "sockets": "3", "items": "Helm", "runes": "Fal + Ko + Um", "stats": "+1 to All Skills\n+Level 9 Meditation When Equipped\n+20-30 faster cast rate\n+10-20 Faster Hit Recovery\n+160% Enhanced Defense\n+10 Increased Chance of Blocking\n+10 to strength\n+10 to dexterity\n+15 all resistances"},
            {"name": "Call to battle", "sockets": "5", "items": "weapon", "runes": "Ohm + Lo + Amn + Ohm + Mal", "stats": "+2 to All Skills\n+40% Faster Cast Rate\n+40% Increased Attack Speed\n+250–290% Enhanced Damage\n6–8 To Battle Command\n6–8 To Battle Orders\n6–8 Shout\n+50% Enhanced Damage\n+20% Deadly Strike\n+7% Life Stolen Per Hit\n+50% Enhanced Damage\nPrevent Monster Heal"},
            {"name": "Dawnbreaker", "sockets": "4", "items": "weapon", "runes": "Amn + Shael + Fal + Pul", "stats": "10% to cast level 30 Lower resist on striking\nAura level 7-15 Cleansing when equipped\n+10-15% Crushing blow\n+150% Enhanced Damage\n+10 strength\n+20% Increased Attack Speed\n+7% Life Stolen Per Hit\n+75% damage to Demons"},
            {"name": "Nemesis", "sockets": "4", "items": "shield", "runes": "Um + Cham + Ber + JEWEL", "stats": "+1 to All Skills\n+15–30% Faster Cast Rate\n+20–30% Increased Chance to Block\n19% to Cast Level 22 Lower Resist When Struck\nLevel 09–12 Conviction When Equipped\n160–240% Enhanced Defense\nAttacker Takes Damage of 155\n+22% to all Resistance\nCannot Be Frozen\nDamage Reduced by 8%\n+Jewel Atributes"},
            {"name": "Achilles Spaar", "sockets": "3", "items": "Javelin / Spear / Polearm", "runes": "Vex + Shael + Ber", "stats": "+3 Javelins & Spears Skills (Amazon Only)\nLevel 13-18 Fanaticism Aura When Equipped\n+3 to Fend\n+3 to Jab\n290-370% Enhanced Damage\n15% to Cast Level 6 Amplify Damage On Striking\n7% to Mana Stolen per Hit\n+20% Increased Attack Speed\n+10 to Strength"},
            {"name": "Legion", "sockets": "6", "items": "Weapon", "runes": "Ber + Lo + Jah + Mal + Hel + Zod", "stats": "Lvl 12 Heart of Wolverine aura when equipped\n+500 to Attack Rating\n+50% Increased Attack Speed\n+450% Enhanced Damage\n+30% Deadly Strike\nDamage reduced by 10%\n20% Crushing Blow\n20% Deadly Strike\nIgnores Target Defense\nPrevent Monster Heal\n-20% Requirements\nIndestructible"},
            {"name": "Fibonacci", "sockets": "2", "items": "Class Item", "runes": "Um + Ohm", "stats": "+3 to all Skills\n20% Faster Cast Rate\n1-3 to Conviction\nSlain Monsters Rest in Peace\n+10 Life After Each Kill\n+10 Mana After Each Kill\n25% Open Wounds (Weapon) / 15% All resist (Armor) / 22% all Resist (Shield)\n50% Enhanced Damage (Weapon) / +5% Max Cold Resist (Armor/Shield)"},
            {"name": "Singularity", "sockets": "3", "items": "Polearm / Bow / Crossbow", "runes": "Zod + Jah + Lo", "stats": "+3 to all Skills\n+30% Faster Cast Rate\n40% Increased Attack Speed\n5% to Cast Level 12 Fade When Struck\nLvl 20-24 Conviction Aura When Equipped\n+300-450% Enhanced Damage\nSlows Target by 20%\nIndestructible\nIgnores Target Defense\n20% Deadly Strike"},
            {"name": "Pillar of Creation", "sockets": "3", "items": "Shield", "runes": "Lo + Jah + Zod", "stats": "+2 to all Skills\n+56% Faster Block Rate\n+30% Chance to Block\n+250-320% Enhanced Defense\n+10-20 to All Attributes\n+70 to All Resistances\nDamage Reduced by 25%\n+5% to maximum resist Lightning\n+50 to Life\nIndestructible"},
            {"name": "Sloth", "sockets": "3", "items": "Helm / Shield", "runes": "Um + Ber + Um", "stats": "20% to Cast Level 16 Corpse Explosion On Attack\n-20% Increased Attack Speed\n-20% Faster Cast Rate\n150-200% Enhanced Defense\n10 to All Attributes\nIncrease Maximum Life 10-15%\n10% to Maximum All Resists\n15% to all Resistance\nDamage Reduced by 8%\n15% to all Resistance"}
        ]
        
        # Breakpoints Database
        self.breakpoints_db = {
            "Sorceress": (
                "=== SORCERESS (Feiticeira) ===\n\n"
                "FASTER CAST RATE (FCR) - Conjuração Normal:\n"
                "  Frame | FCR Necessário\n"
                "    13  | 0%\n"
                "    12  | 9%\n"
                "    11  | 20%\n"
                "    10  | 37%\n"
                "     9  | 63%\n"
                "     8  | 105%  <-- Meta principal recomendada\n"
                "     7  | 200%\n\n"
                "FCR para Lightning & Chain Lightning:\n"
                "  Frame | FCR Necessário\n"
                "    19  | 0%\n"
                "    16  | 23%\n"
                "    15  | 35%\n"
                "    14  | 52%\n"
                "    13  | 78%\n"
                "    12  | 117% <-- Meta principal para Raio\n"
                "    11  | 194%\n\n"
                "FASTER HIT RECOVERY (FHR) - Recuperação:\n"
                "  Frame | FHR Necessário\n"
                "    15  | 0%\n"
                "    11  | 20%\n"
                "     9  | 42%\n"
                "     8  | 60%  <-- Excelente custo-benefício\n"
                "     7  | 86%  <-- Meta ideal PvP / End-game\n"
                "     6  | 142%\n\n"
                "FASTER BLOCK RATE (FBR) - Velocidade de Bloqueio:\n"
                "  Frame | FBR Necessário\n"
                "     9  | 0%\n"
                "     7  | 15%\n"
                "     6  | 27%\n"
                "     5  | 48%\n"
                "     4  | 86%"
            ),
            "Paladin": (
                "=== PALADIN (Paladino) ===\n\n"
                "FASTER CAST RATE (FCR) - Teleport / Blessed Hammer:\n"
                "  Frame | FCR Necessário\n"
                "    15  | 0%\n"
                "    14  | 9%\n"
                "    13  | 18%\n"
                "    12  | 30%\n"
                "    11  | 48%\n"
                "    10  | 75%  <-- Meta inicial Hammerdin\n"
                "     9  | 125% <-- Meta perfeita End-game\n\n"
                "FASTER HIT RECOVERY (FHR) - Recuperação:\n"
                "  Frame | FHR Necessário\n"
                "     9  | 0%\n"
                "     7  | 15%\n"
                "     6  | 27%\n"
                "     5  | 48%  <-- Meta básica sugerida\n"
                "     4  | 86%  <-- Meta recomendada\n"
                "     3  | 200%\n\n"
                "FASTER BLOCK RATE (FBR) - Com Holy Shield ativo:\n"
                "  Frame | FBR Necessário\n"
                "     2  | 0%   <-- Padrão instantâneo com Holy Shield!\n"
                "     1  | 86%"
            ),
            "Necromancer": (
                "=== NECROMANCER (Necromante) ===\n\n"
                "FASTER CAST RATE (FCR) - Conjuração:\n"
                "  Frame | FCR Necessário\n"
                "    15  | 0%\n"
                "    14  | 9%\n"
                "    13  | 18%\n"
                "    12  | 30%\n"
                "    11  | 48%\n"
                "    10  | 75%  <-- Meta ideal inicial\n"
                "     9  | 125% <-- Meta final (Teleport rápido)\n\n"
                "FASTER HIT RECOVERY (FHR) - Recuperação:\n"
                "  Frame | FHR Necessário\n"
                "    13  | 0%\n"
                "    10  | 20%\n"
                "     9  | 29%\n"
                "     8  | 39%\n"
                "     7  | 56%  <-- Custo-benefício excelente\n"
                "     6  | 86%  <-- Meta end-game recomendada\n"
                "     5  | 152%"
            ),
            "Amazon": (
                "=== AMAZON (Amazona) ===\n\n"
                "FASTER CAST RATE (FCR) - (Conjuradora lenta):\n"
                "  Frame | FCR Necessário\n"
                "    19  | 0%\n"
                "    17  | 7%\n"
                "    16  | 13%\n"
                "    15  | 22%\n"
                "    14  | 32%\n"
                "    13  | 48%\n"
                "    12  | 68%  <-- Meta final aceitável\n"
                "    11  | 99%\n"
                "    10  | 152%\n\n"
                "FASTER HIT RECOVERY (FHR) - Recuperação:\n"
                "  Frame | FHR Necessário\n"
                "    11  | 0%\n"
                "     9  | 13%\n"
                "     8  | 20%\n"
                "     7  | 32%  <-- Meta básica\n"
                "     6  | 52%  <-- Meta recomendada\n"
                "     5  | 86%  <-- Ideal end-game\n"
                "     4  | 174%"
            ),
            "Barbarian": (
                "=== BARBARIAN (Bárbaro) ===\n\n"
                "FASTER CAST RATE (FCR) - Gritos e Teleport:\n"
                "  Frame | FCR Necessário\n"
                "    13  | 0%\n"
                "    12  | 9%\n"
                "    11  | 20%\n"
                "    10  | 37%\n"
                "     9  | 63%\n"
                "     8  | 105% <-- Velocidade idêntica à Sorceress!\n"
                "     7  | 200%\n\n"
                "FASTER HIT RECOVERY (FHR) - Recuperação:\n"
                "  Frame | FHR Necessário\n"
                "     9  | 0%\n"
                "     7  | 15%\n"
                "     6  | 27%\n"
                "     5  | 48%  <-- Meta ideal padrão\n"
                "     4  | 86%  <-- Meta final\n"
                "     3  | 200%"
            ),
            "Druid": (
                "=== DRUID (Druida - Forma Humana) ===\n\n"
                "FASTER CAST RATE (FCR) - Tornados / Magias:\n"
                "  Frame | FCR Necessário\n"
                "    18  | 0%\n"
                "    15  | 10%\n"
                "    14  | 19%\n"
                "    13  | 30%\n"
                "    12  | 46%\n"
                "    11  | 68%  <-- Meta inicial Wind Druid\n"
                "    10  | 99%  <-- Meta principal recomendada\n"
                "     9  | 163%\n\n"
                "FASTER HIT RECOVERY (FHR) - Recuperação:\n"
                "  Frame | FHR Necessário\n"
                "    14  | 0%\n"
                "    11  | 9%\n"
                "     9  | 19%\n"
                "     8  | 29%\n"
                "     7  | 42%  <-- Meta básica\n"
                "     6  | 63%  <-- Meta recomendada\n"
                "     5  | 99%  <-- Ideal End-game\n"
                "     4  | 174%"
            ),
            "Assassin": (
                "=== ASSASSIN (Assassina) ===\n\n"
                "FASTER CAST RATE (FCR) - Conjuração:\n"
                "  Frame | FCR Necessário\n"
                "    16  | 0%\n"
                "    15  | 8%\n"
                "    14  | 16%\n"
                "    13  | 27%\n"
                "    12  | 42%\n"
                "    11  | 65%  <-- Meta padrão confortável\n"
                "    10  | 102% <-- Meta final de Teleport\n"
                "     9  | 174%\n\n"
                "FASTER HIT RECOVERY (FHR) - Recuperação:\n"
                "  Frame | FHR Necessário\n"
                "     9  | 0%\n"
                "     7  | 15%\n"
                "     6  | 27%\n"
                "     5  | 48%  <-- Meta recomendada\n"
                "     4  | 86%  <-- Meta final PvP\n"
                "     3  | 200%"
            )
        }
        
        # Farm Areas Database (Level 85 Hell Zones)
        self.farm_db = {
            "Act 1 - The Pit (O Fosso)": (
                "ZONA DE FARM: The Pit (Fosso - Planalto de Tamoe)\n"
                "Nível do Mapa: 85 (Hell)\n"
                "Imunidades Frequentes: Fogo (Fire), Gelo (Cold), Raio (Lightning)\n"
                "Recomendado Para: Bowazon, Hammerdin, Wind Druid, Poison Necro\n"
                "Dica: Uma das áreas mais populares e lucrativas. Monstros fracos com pouca vida."
            ),
            "Act 1 - Mausoleum (Mausoléu)": (
                "ZONA DE FARM: Mausoleum (Cemitério da Raven)\n"
                "Nível do Mapa: 85 (Hell)\n"
                "Imunidades Frequentes: Apenas Raio (Lightning)\n"
                "Recomendado Para: Sorceress de Gelo (Blizzard), Sorceress de Fogo\n"
                "Dica: Velocidade de movimento dos monstros é muito baixa. Área extremamente segura para personagens iniciais com equipamentos básicos."
            ),
            "Act 2 - Ancient Tunnels (Túneis Antigos)": (
                "ZONA DE FARM: Ancient Tunnels (Lost City - Cidade Perdida)\n"
                "Nível do Mapa: 85 (Hell)\n"
                "Imunidades Frequentes: Raio (Lightning), Fogo (Fire), Veneno (Poison)\n"
                "Recomendado Para: Sorceress de Gelo (Blizzard) - Imbatível aqui!\n"
                "Dica: **NÃO possui imunes a Gelo nativos**. É o melhor local de farm do jogo para Sorceress Blizzard."
            ),
            "Act 2 - Stony Tomb (Tumba de Pedra)": (
                "ZONA DE FARM: Stony Tomb (Rocky Waste - Entrada da cidade)\n"
                "Nível do Mapa: 85 (Hell)\n"
                "Imunidades Frequentes: Gelo (Cold), Raio (Lightning)\n"
                "Recomendado Para: Sorceress de Fogo (Hydra/Fireball), Hammerdin\n"
                "Dica: Área super próxima à cidade do Act 2. Poucos monstros imunes a Fogo, excelente farm."
            ),
            "Act 3 - Arachnid Lair (Caverna da Aranha)": (
                "ZONA DE FARM: Arachnid Lair (Spider Forest - Próximo ao Waypoint)\n"
                "Nível do Mapa: 85 (Hell)\n"
                "Imunidades Frequentes: Raio (Lightning), Gelo (Cold)\n"
                "Recomendado Para: Sorceress de Fogo, Javazona, Necromancer\n"
                "Dica: Mapa muito denso, compacto e do lado do Waypoint da floresta. Rápido e prático."
            ),
            "Act 4 - Chaos Sanctuary (Santuário do Caos)": (
                "ZONA DE FARM: Chaos Sanctuary (Rio de Fogo / Diablo)\n"
                "Nível do Mapa: 85 (Hell)\n"
                "Imunidades Frequentes: Todas (Gelo, Fogo, Raio, Veneno e Físico)\n"
                "Recomendado Para: Hammerdin, FoH Paladin, Javazona, Necromancer Poison, Sorceress Infinity\n"
                "Dica: Área com maior densidade de XP e drops do jogo. Muito perigoso sem resistências adequadas."
            ),
            "Act 5 - Throne of Destruction (Trono)": (
                "ZONA DE FARM: Throne of Destruction (Trono do Baal)\n"
                "Nível do Mapa: 85 (Hell)\n"
                "Imunidades Frequentes: Variadas (Varia de acordo com os spawns)\n"
                "Recomendado Para: Personagens bem equipados (End-game)\n"
                "Dica: Melhor local para farmar experiência e subir de nível (XP). As ondas de lacaios dão muita XP."
            )
        }
        
        # Build Guides Database
        self.builds_db = {
            "Sorc_Fire": (
                "              Sorceress (Arcanista)\n"
                "## Fire Sorceress.\n\n"
                "* Skills:\n"
                "Fireburst LV20.\n"
                "Fire Bolt LV20.\n"
                "Fire Mastery LV20.\n"
                "Teleport LV1.\n"
                "Warmth LV1.\n"
                "Thunder Storm LV20.\n"
                "Lightning Mastery LV17.\n\n"
                "* Itens:\n"
                "Grimório The Oculus,\n"
                "Escudo Spirit,\n"
                "Armadura Skin of the Vipermagi,\n"
                "Magefist.\n\n"
                "*Hire\n"
                "Vapire gaze.\n"
                "Arma Infinity (no mercenário para quebrar imunidade)\n\n"
                "* Farm:\n"
                "Andariel,\n"
                "Mephisto,\n"
                "vacas (Secret Cow Level)\n"
                "Arachnid Lair."
            ),
            "Sorc_Ice": (
                "Ice Sorceress (Frost Nova)\n\n"
                "* Skills:\n"
                "Frost Nova LV20.\n"
                "Cold Mastery LV20.\n"
                "Shiver Armo LV20.\n"
                "Fronze Armo Lv20.\n"
                "Chilling Armo Lv20.\n"
                "Teleport LV1.\n"
                "Warmth LV1.\n\n"
                "* Itens:\n"
                "Espada Death's Fathom,\n"
                "Escudo Spirit,\n"
                "Armadura Ormus' Robes,\n"
                "Luvas Magefist.\n\n"
                "*Hire\n"
                "Vapire gaze.\n"
                "Arma Infinity (no mercenário para quebrar imunidade)\n\n"
                "* Farm:\n"
                "Ancient Tunnels (sem imunes a gelo),\n"
                "Mephisto e Andariel."
            ),
            "Sorc_Light": (
                "Light Sorceress\n\n"
                "* Skills:\n"
                "Nova LV20.\n"
                "Thunder Storm LV20.\n"
                "Lightning Mastery LV20.\n"
                "Shiver Armo LV20.\n"
                "Cold Mastery LV15.\n"
                "Chilling Armo LV1.\n"
                "Fronze Armo Lv1.\n"
                "Teleport LV1.\n"
                "Warmth LV1.\n\n"
                "* Itens:\n"
                "RW Storm <Tir + Ort>\n"
                "Griffon's Eye,\n"
                "Armadura Ormus' Robes,\n"
                "Luvas Magefist.\n\n"
                "*Hire\n"
                "Vapire gaze.\n"
                "Arma Infinity (no mercenário para quebrar imunidade).\n\n"
                "* Farm:\n"
                "The Countess.\n"
                "The Summoner.\n"
                "Chaos Sanctuary.\n"
                "Baal."
            ),
            "Pala_Hammer": (
                "Paladin\n"
                "## Hammerdin Build\n\n"
                "* Skills:\n"
                "Blessed Hammer LV20.\n"
                "Vigor LV20.\n"
                "Blessed Aim LV20.\n"
                "Concentration LV20.\n"
                "Holy Shield LV20.\n\n"
                "* Itens:\n"
                "RW Enigma,\n"
                "Arma Heart of the Oak (Hoto),\n"
                "Escudo Spirit em base de Paladino.\n\n"
                "* Farm:\n"
                "Chaos Sanctuary,\n"
                "Travincal,\n"
                "Baal e Pit. Excelente em quase todo o jogo."
            ),
            "Pala_Zeal": (
                "Zeal + Auradin\n\n"
                "* Skills:\n"
                "Zeal LV20.\n"
                "Sacrifice LV20.\n"
                "Conviction (Aura ativa) somando os itens ate LV25.\n"
                "Holy Shield LV20.\n"
                "Resist Cold LV20.\n"
                "Savation oque sobrar.\n\n"
                "* Itens:\n"
                "Arma RW Doom <HEL + OHM + UM + LO + CHAM>.\n"
                "Escudo Talus'ar.\n"
                "Armadura RW <Cham + Dol + Um + Ber>.\n"
                "Helm Viper RW <Ist + Lo + Ohm>.\n"
                "Cinto al'meish.\n"
                "Botas Sandstorm Trek\n"
                "Vampirebone Gloves\n"
                "Ring Carrion Wind\n"
                "Amulet Telling of Beads\n\n"
                "* Farm:\n"
                "Travincal.\n"
                "Uber Tristram (foco em chefes).\n"
                "Chaos Sanctuary."
            ),
            "Pala_Aura": (
                "Auradin (Dragondin / Tesladin)\n\n"
                "* Skills:\n"
                "Resist Fire LV20.\n"
                "Salvation LV20.\n"
                "Conviction (Aura ativa) LV25+ com itens.\n"
                "Holy Shield LV20.\n\n"
                "* Itens:\n"
                "Escudo e Armadura RW Dragon OU RW Dream.\n"
                "Arma Hand of Justice.\n\n"
                "* Farm:\n"
                "Secret Cow Level.\n"
                "Flayer Jungle.\n"
                "Chaos Sanctuary."
            ),
            "Ama_Bow": (
                "Cold Bow (Frost Arrow)\n\n"
                "* Skills:\n"
                "Freezing Arrow LV20.\n"
                "Cold Arrow LV20.\n"
                "Ice Arrow LV20.\n"
                "Penetrate LV20.\n"
                "Pierce alto.\n\n"
                "* Itens:\n"
                "Arco Ice.\n"
                "Armadura Enigma ou Fortitude.\n"
                "Luvas com +Bow Skills e IAS.\n\n"
                "* Farm:\n"
                "Ancient Tunnels.\n"
                "The Pit.\n"
                "Flayer Jungle."
            ),
            "Ama_Light": (
                "Lightning Fury (Javazona)\n\n"
                "* Skills:\n"
                "Lightning Fury LV20.\n"
                "Charged Strike LV20.\n"
                "Lightning Strike LV20.\n"
                "Power Strike LV20.\n"
                "Pierce 1+.\n\n"
                "* Itens:\n"
                "Titan's Revenge.\n"
                "Escudo Spirit ou Phoenix.\n"
                "Griffon's Eye.\n"
                "Luvas +3 Javelin.\n\n"
                "* Farm:\n"
                "Secret Cow Level.\n"
                "Chaos Sanctuary.\n"
                "Baal."
            ),
            "Druid_Fire": (
                "Fire Druid\n\n"
                "* Skills:\n"
                "Fissure LV20.\n"
                "Volcano LV20.\n"
                "Firestorm LV20.\n"
                "Molten Boulder LV20.\n"
                "Oak Sage LV20.\n\n"
                "* Itens:\n"
                "Ravenlore.\n"
                "Flickering Flame.\n"
                "Escudo Phoenix.\n"
                "Armadura Enigma.\n\n"
                "* Farm:\n"
                "Stony Tomb.\n"
                "Arachnid Lair.\n"
                "Secret Cow Level."
            ),
            "Druid_Wind": (
                "Wind Druid (Tornado)\n\n"
                "* Skills:\n"
                "Tornado LV20.\n"
                "Hurricane LV20.\n"
                "Twister LV20.\n"
                "Cyclone Armor LV20.\n"
                "Oak Sage LV20.\n\n"
                "* Itens:\n"
                "Heart of the Oak.\n"
                "Jalal's ou raro +5 Tornado.\n"
                "Escudo Spirit.\n"
                "Armadura Enigma.\n\n"
                "* Farm:\n"
                "Chaos Sanctuary.\n"
                "Baal.\n"
                "The Pit.\n"
                "Travincal."
            ),
            "Barb_WW": (
                "Whirlwind (WW)\n\n"
                "* Skills:\n"
                "Whirlwind LV20.\n"
                "Battle Orders LV20.\n"
                "Weapon Mastery LV20.\n"
                "Shout LV20.\n\n"
                "* Itens:\n"
                "Grief (x2) ou BOTD.\n"
                "Armadura Fortitude.\n"
                "Luvas Lay on Hands.\n\n"
                "* Farm:\n"
                "Travincal.\n"
                "Chaos Sanctuary.\n"
                "The Pit."
            ),
            "Barb_Zerk": (
                "Barbarian\n"
                "## Berserk (Pit Finder)\n\n"
                "* Skills:\n"
                "Berserk LV20.\n"
                "Howl LV20.\n"
                "Battle Orders LV20.\n"
                "Mastery LV20.\n"
                "Find Item alto.\n\n"
                "* Itens:\n"
                "Grief.\n"
                "Blade of Ali Baba (switch).\n"
                "Armadura Enigma.\n\n"
                "* Farm:\n"
                "The Pit.\n"
                "Travincal."
            ),
            "Nec_Summon": (
                "Summon Necro\n\n"
                "* Skills:\n"
                "Raise Skeleton LV20.\n"
                "Skeleton Mastery LV20.\n"
                "Corpse Explosion LV20.\n"
                "Amplify Damage 1.\n"
                "Clay Golem 1.\n\n"
                "* Itens:\n"
                "Beast.\n"
                "Armadura Enigma.\n"
                "Homunculus ou Spirit.\n\n"
                "* Farm:\n"
                "Chaos Sanctuary.\n"
                "Secret Cow Level.\n"
                "The Pit.\n"
                "Nihlathak."
            ),
            "Nec_Poison": (
                "Poison Nova\n\n"
                "* Skills:\n"
                "Poison Nova LV20.\n"
                "Poison Explosion LV20.\n"
                "Poison Dagger LV20.\n"
                "Lower Resist 1+.\n\n"
                "* Itens:\n"
                "Death's Web.\n"
                "Trang-Oul's Wing.\n"
                "Armadura Enigma.\n\n"
                "* Farm:\n"
                "Secret Cow Level.\n"
                "The Pit.\n"
                "Arachnid Lair."
            ),
            "Ass_Trap": (
                "Trap Assassin\n\n"
                "* Skills:\n"
                "Lightning Sentry LV20.\n"
                "Death Sentry LV20.\n"
                "Charged Bolt Sentry LV20.\n"
                "Shock Web LV20.\n"
                "Burst of Speed 1.\n\n"
                "* Itens:\n"
                "Garras +3 Trap.\n"
                "Escudo Spirit.\n"
                "Enigma ou Treachery.\n"
                "Griffon's Eye.\n\n"
                "* Farm:\n"
                "Secret Cow Level.\n"
                "The Pit.\n"
                "Chaos Sanctuary.\n"
                "Nihlathak."
            )
        }
        
        # Sub-class buttons mapping
        self.sub_buttons = {}
        self.active_class_tab = ""
        
        # Initialize UI Tabs
        self.show_builds_tab()
        
    def create_sidebar_btn(self, text, command, y_pos):
        btn = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            bg="#12131a",
            fg="#8a99ad",
            activebackground="#ff2a2a",
            activeforeground="#ffffff",
            bd=1,
            relief="raised",
            highlightthickness=0,
            font=("Yu Gothic UI", 8, "bold"),
            cursor="hand2"
        )
        btn.place(x=5, y=y_pos, width=120, height=28)
        
        btn.bind("<Enter>", lambda e: btn.configure(bg="#1c1d29", fg="#ffffff", relief="flat"))
        btn.bind("<Leave>", lambda e: btn.configure(bg="#12131a", fg="#8a99ad", relief="raised"))
        return btn

    def create_flat_button(self, parent, text, command, x, y, w, h=25):
        btn = tk.Button(
            parent, 
            text=text, 
            command=command,
            bg="#12131a", 
            fg="#8a99ad", 
            activebackground="#ff2a2a", 
            activeforeground="#ffffff",
            bd=1, 
            relief="raised",
            highlightthickness=0,
            font=("Yu Gothic UI", 9, "bold"),
            cursor="hand2"
        )
        btn.place(x=x, y=y, width=w, height=h)
        
        btn.bind("<Enter>", lambda e: btn.configure(bg="#1c1d29", fg="#ffffff", relief="flat"))
        btn.bind("<Leave>", lambda e: btn.configure(bg="#12131a", fg="#8a99ad", relief="raised"))
        return btn

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ==================== TAB 1: BUILDS ====================
    def show_builds_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        # Header title
        tk.Label(
            self.content_frame,
            text="GUIAS DE BUILDS (CLASSES)",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        # Builds content frame
        self.builds_panel = tk.Frame(self.content_frame, bg="#0b0c10", width=410, height=440)
        self.builds_panel.place(x=0, y=35, width=410, height=440)
        
        # Class Selection Buttons
        self.create_flat_button(self.builds_panel, "Sorceress", self.build_sorc, 10, 5, 120)
        self.create_flat_button(self.builds_panel, "Paladin", self.build_pala, 140, 5, 120)
        self.create_flat_button(self.builds_panel, "Amazon", self.build_ama, 270, 5, 120)
        
        self.create_flat_button(self.builds_panel, "Barbarian", self.build_barb, 10, 35, 120)
        self.create_flat_button(self.builds_panel, "Necromancer", self.build_nec, 140, 35, 120)
        self.create_flat_button(self.builds_panel, "Assassin", self.build_ass, 270, 35, 120)
        
        self.create_flat_button(self.builds_panel, "Druid", self.build_druid, 140, 65, 120)
        
        # Sub-class selector buttons mapping
        self.sub_buttons = {
            "Sorc": [
                self.create_flat_button(self.builds_panel, "FIRE", lambda: self.show_guide("Sorc_Fire"), 10, 100, 120),
                self.create_flat_button(self.builds_panel, "ICE", lambda: self.show_guide("Sorc_Ice"), 140, 100, 120),
                self.create_flat_button(self.builds_panel, "LIGHT", lambda: self.show_guide("Sorc_Light"), 270, 100, 120)
            ],
            "Pala": [
                self.create_flat_button(self.builds_panel, "HAMMER", lambda: self.show_guide("Pala_Hammer"), 10, 100, 120),
                self.create_flat_button(self.builds_panel, "ZEAL", lambda: self.show_guide("Pala_Zeal"), 140, 100, 120),
                self.create_flat_button(self.builds_panel, "AURA", lambda: self.show_guide("Pala_Aura"), 270, 100, 120)
            ],
            "Ama": [
                self.create_flat_button(self.builds_panel, "BOW", lambda: self.show_guide("Ama_Bow"), 10, 100, 120),
                self.create_flat_button(self.builds_panel, "LIGHT FURY", lambda: self.show_guide("Ama_Light"), 140, 100, 120)
            ],
            "Druid": [
                self.create_flat_button(self.builds_panel, "FIRE", lambda: self.show_guide("Druid_Fire"), 10, 100, 120),
                self.create_flat_button(self.builds_panel, "WIND", lambda: self.show_guide("Druid_Wind"), 140, 100, 120)
            ],
            "Barb": [
                self.create_flat_button(self.builds_panel, "WHIRLWIND", lambda: self.show_guide("Barb_WW"), 10, 100, 120),
                self.create_flat_button(self.builds_panel, "ZERK", lambda: self.show_guide("Barb_Zerk"), 140, 100, 120)
            ],
            "Nec": [
                self.create_flat_button(self.builds_panel, "SUMMON", lambda: self.show_guide("Nec_Summon"), 10, 100, 120),
                self.create_flat_button(self.builds_panel, "POISON", lambda: self.show_guide("Nec_Poison"), 140, 100, 120)
            ],
            "Ass": [
                self.create_flat_button(self.builds_panel, "TRAPS", lambda: self.show_guide("Ass_Trap"), 10, 100, 120)
            ]
        }
        
        self.hide_all_subs()
        
        # Text Frame & Widget for Guide Content (Modernized Style)
        txt_frame = tk.Frame(self.builds_panel, bg="#12131a", bd=1, relief="solid")
        txt_frame.place(x=10, y=135, width=380, height=295)
        
        self.text_info = tk.Text(
            txt_frame, 
            bg="#050608", 
            fg="#f0f3f8", 
            insertbackground="#ffffff", 
            font=("Consolas", 10),
            bd=0,
            padx=10, 
            pady=10
        )
        self.text_info.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(txt_frame, orient="vertical", command=self.text_info.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_info.configure(yscrollcommand=scrollbar.set)
        
        self.set_text("SELECIONE UMA CLASSE ACIMA PARA EXIBIR OS GUIAS DE BUILDS.")
        
    def hide_all_subs(self):
        for btn_list in self.sub_buttons.values():
            for btn in btn_list:
                btn.place_forget()
                
    def show_subs_for(self, key):
        self.hide_all_subs()
        if key in self.sub_buttons:
            for idx, btn in enumerate(self.sub_buttons[key]):
                x_pos = 10 + (idx * 130)
                btn.place(x=x_pos, y=100, width=120, height=25)
                
    def set_text(self, text):
        self.text_info.configure(state="normal")
        self.text_info.delete("1.0", tk.END)
        self.text_info.insert(tk.END, text)
        self.text_info.configure(state="disabled")
        
    def build_sorc(self):
        self.active_class_tab = "Sorc"
        self.show_subs_for("Sorc")
        self.set_text("SORCERESS BUILDS")
        
    def build_pala(self):
        self.active_class_tab = "Pala"
        self.show_subs_for("Pala")
        self.set_text("PALADIN BUILDS")
        
    def build_ama(self):
        self.active_class_tab = "Ama"
        self.show_subs_for("Ama")
        self.set_text("AMAZON BUILDS")
        
    def build_druid(self):
        self.active_class_tab = "Druid"
        self.show_subs_for("Druid")
        self.set_text("DRUID BUILDS")
        
    def build_barb(self):
        self.active_class_tab = "Barb"
        self.show_subs_for("Barb")
        self.set_text("BARBARIAN BUILDS")
        
    def build_nec(self):
        self.active_class_tab = "Nec"
        self.show_subs_for("Nec")
        self.set_text("NECROMANCER BUILDS")
        
    def build_ass(self):
        self.active_class_tab = "Ass"
        self.show_subs_for("Ass")
        self.set_text("ASSASSIN BUILDS")
        
    def show_guide(self, guide_key):
        expected_state = guide_key.split("_")[0]
        if expected_state != self.active_class_tab:
            return
        guide_text = self.builds_db.get(guide_key, "")
        self.set_text(guide_text)

    # ==================== TAB 2: RUNEWORDS ====================
    def show_runewords_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="GUIA DE PALAVRAS RÚNICAS (RUNEWORDS)",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        # Search Box
        tk.Label(
            self.content_frame,
            text="Buscar:",
            fg="#8a99ad",
            bg="#0b0c10",
            font=("Yu Gothic UI", 9, "bold")
        ).place(x=10, y=38)
        
        self.rw_search_var = tk.StringVar()
        self.rw_search_var.trace_add("write", lambda *args: self.filter_runewords())
        
        search_entry = tk.Entry(
            self.content_frame,
            textvariable=self.rw_search_var,
            bg="#12131a",
            fg="#ffffff",
            bd=1,
            relief="solid",
            insertbackground="#ffffff",
            font=("Yu Gothic UI", 9)
        )
        search_entry.place(x=60, y=38, width=150, height=22)
        
        # Scrollable list of runewords
        list_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        list_frame.place(x=10, y=70, width=150, height=395)
        
        self.rw_listbox = tk.Listbox(
            list_frame,
            bg="#050608",
            fg="#8a99ad",
            selectbackground="#ff2a2a",
            selectforeground="#ffffff",
            bd=0,
            font=("Yu Gothic UI", 9, "bold"),
            highlightthickness=0
        )
        self.rw_listbox.pack(side="left", fill="both", expand=True)
        self.rw_listbox.bind("<<ListboxSelect>>", self.on_runeword_select)
        
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.rw_listbox.yview)
        sb.pack(side="right", fill="y")
        self.rw_listbox.configure(yscrollcommand=sb.set)
        
        # Description box on right
        desc_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        desc_frame.place(x=170, y=70, width=230, height=395)
        
        self.rw_text = tk.Text(
            desc_frame,
            bg="#050608",
            fg="#f0f3f8",
            bd=0,
            padx=10,
            pady=10,
            font=("Consolas", 9),
            wrap="word"
        )
        self.rw_text.pack(fill="both", expand=True)
        
        # Populate initially
        self.filter_runewords()
        
    def filter_runewords(self):
        query = self.rw_search_var.get().lower()
        self.rw_listbox.delete(0, tk.END)
        self.rw_filtered_list = []
        
        for rw in self.runewords_db:
            if (query in rw["name"].lower() or 
                query in rw["runes"].lower() or 
                query in rw["items"].lower() or 
                query in rw["sockets"].lower() or
                query in rw["stats"].lower()):
                self.rw_listbox.insert(tk.END, rw["name"])
                self.rw_filtered_list.append(rw)
                
    def on_runeword_select(self, event):
        idx_tuple = self.rw_listbox.curselection()
        if not idx_tuple:
            return
        idx = idx_tuple[0]
        rw = self.rw_filtered_list[idx]
        
        text_content = (
            f"PALAVRA: {rw['name']}\n"
            f"FUROS: {rw['sockets']} Sockets\n"
            f"BASES: {rw['items']}\n"
            f"FÓRMULA: {rw['runes']}\n"
            f"---------------------------------\n"
            f"PROPRIEDADES:\n{rw['stats']}"
        )
        
        self.rw_text.configure(state="normal")
        self.rw_text.delete("1.0", tk.END)
        self.rw_text.insert(tk.END, text_content)
        self.rw_text.configure(state="disabled")

    # ==================== TAB 3: BREAKPOINTS ====================
    def show_breakpoints_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="LIMITES DE VELOCIDADE (BREAKPOINTS)",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        # Buttons for classes
        classes = ["Sorceress", "Paladin", "Necromancer", "Amazon", "Barbarian", "Druid", "Assassin"]
        for idx, cls in enumerate(classes):
            x_pos = 10 + (idx % 3) * 130
            y_pos = 38 + (idx // 3) * 32
            self.create_flat_button(self.content_frame, cls, lambda c=cls: self.show_class_breakpoints(c), x_pos, y_pos, 120)
            
        # Display Box
        disp_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        disp_frame.place(x=10, y=135, width=390, height=330)
        
        self.bp_text = tk.Text(
            disp_frame,
            bg="#050608",
            fg="#f0f3f8",
            bd=0,
            padx=10,
            pady=10,
            font=("Consolas", 9)
        )
        self.bp_text.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(disp_frame, orient="vertical", command=self.bp_text.yview)
        sb.pack(side="right", fill="y")
        self.bp_text.configure(yscrollcommand=sb.set)
        
        self.show_class_breakpoints("Sorceress")
        
    def show_class_breakpoints(self, cls_name):
        text_content = self.breakpoints_db.get(cls_name, "Nenhum dado encontrado.")
        self.bp_text.configure(state="normal")
        self.bp_text.delete("1.0", tk.END)
        self.bp_text.insert(tk.END, text_content)
        self.bp_text.configure(state="disabled")

    # ==================== TAB 4: FARM AREAS ====================
    def show_farm_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="ÁREAS DE FARM HELL (LIVEL 85)",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        # Farm Listbox
        list_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        list_frame.place(x=10, y=38, width=170, height=427)
        
        self.farm_listbox = tk.Listbox(
            list_frame,
            bg="#050608",
            fg="#8a99ad",
            selectbackground="#ff2a2a",
            selectforeground="#ffffff",
            bd=0,
            font=("Yu Gothic UI", 8, "bold"),
            highlightthickness=0
        )
        self.farm_listbox.pack(side="left", fill="both", expand=True)
        self.farm_listbox.bind("<<ListboxSelect>>", self.on_farm_select)
        
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.farm_listbox.yview)
        sb.pack(side="right", fill="y")
        self.farm_listbox.configure(yscrollcommand=sb.set)
        
        # Description box on right
        desc_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        desc_frame.place(x=190, y=38, width=210, height=427)
        
        self.farm_text = tk.Text(
            desc_frame,
            bg="#050608",
            fg="#f0f3f8",
            bd=0,
            padx=10,
            pady=10,
            font=("Yu Gothic UI", 9),
            wrap="word"
        )
        self.farm_text.pack(fill="both", expand=True)
        
        # Populate
        self.farm_keys = list(self.farm_db.keys())
        for key in self.farm_keys:
            self.farm_listbox.insert(tk.END, key)
            
        self.farm_listbox.selection_set(0)
        self.on_farm_select(None)
        
    def on_farm_select(self, event):
        idx_tuple = self.farm_listbox.curselection()
        if not idx_tuple:
            return
        idx = idx_tuple[0]
        key = self.farm_keys[idx]
        text_content = self.farm_db.get(key, "")
        
        self.farm_text.configure(state="normal")
        self.farm_text.delete("1.0", tk.END)
        self.farm_text.insert(tk.END, text_content)
        self.farm_text.configure(state="disabled")

    def on_close(self):
        self.autoclicker_active = False
        self.timer_running = False
        self.app.toolbox_instance = None
        self.root.destroy()

    def autoclicker_loop(self):
        while True:
            if self.autoclicker_active:
                button = self.app.click_button
                speed = self.app.click_speed
                click_mouse(button)
                time.sleep(speed / 1000.0)
            else:
                time.sleep(0.05)

    def trigger_timer_hotkey(self):
        if not self.timer_running:
            self.start_timer()
        else:
            self.next_run()

    def record_split(self):
        if self.timer_running:
            dur = time.time() - self.timer_start_time
            minutes = int(dur // 60)
            seconds = int(dur % 60)
            tenths = int((dur * 10) % 10)
            formatted = f"{minutes:02d}:{seconds:02d}.{tenths}"
            log_debug(f"Split recorded: {formatted}")
            if hasattr(self, 'timer_listbox') and self.timer_listbox.winfo_exists():
                self.timer_listbox.insert(0, f" Split (Cidade)  --->  {formatted}")

    def stop_timer(self):
        if self.timer_running:
            self.pause_timer()

    def trigger_autoclicker_hotkey(self):
        self.toggle_autoclicker()

    # ==================== TAB 5: RUN TIMER ====================
    def show_timer_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="CRONÔMETRO DE RUNS (SPEEDRUN TIMER)",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        # Display Box for Timer
        timer_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        timer_frame.place(x=10, y=40, width=390, height=130)
        
        self.lbl_timer_run = tk.Label(
            timer_frame,
            text=f"RUN #{self.run_count + 1}",
            fg="#ff2a2a",
            bg="#12131a",
            font=("Yu Gothic UI", 10, "bold")
        )
        self.lbl_timer_run.place(x=15, y=10)
        
        self.lbl_timer_clock = tk.Label(
            timer_frame,
            text="00:00.0",
            fg="#ffffff",
            bg="#12131a",
            font=("Consolas", 36, "bold")
        )
        self.lbl_timer_clock.place(x=15, y=30)
        
        # Action Buttons
        self.btn_timer_toggle = self.create_flat_button(
            timer_frame, 
            "INICIAR" if not self.timer_running else "PAUSAR", 
            self.start_timer if not self.timer_running else self.pause_timer, 
            270, 15, 100, 30
        )
        
        self.btn_timer_split = self.create_flat_button(
            timer_frame, 
            "NEXT RUN (Alt+T)", 
            self.next_run, 
            270, 50, 100, 30
        )
        
        self.btn_timer_reset = self.create_flat_button(
            timer_frame, 
            "RESETAR", 
            self.reset_timer, 
            270, 85, 100, 30
        )
        
        # History panel
        history_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        history_frame.place(x=10, y=180, width=390, height=280)
        
        tk.Label(
            history_frame,
            text="HISTÓRICO DE RUNS DA SESSÃO",
            fg="#8a99ad",
            bg="#12131a",
            font=("Yu Gothic UI", 9, "bold")
        ).place(x=10, y=5)
        
        self.lbl_average = tk.Label(
            history_frame,
            text="Tempo Médio: --:--.-",
            fg="#00ff00",
            bg="#12131a",
            font=("Yu Gothic UI", 9, "bold")
        )
        self.lbl_average.place(x=220, y=5)
        
        # List of runs
        list_container = tk.Frame(history_frame, bg="#12131a", bd=1, relief="solid")
        list_container.place(x=10, y=30, width=370, height=235)
        
        self.timer_listbox = tk.Listbox(
            list_container,
            bg="#050608",
            fg="#8a99ad",
            selectbackground="#ff2a2a",
            selectforeground="#ffffff",
            bd=0,
            font=("Consolas", 10),
            highlightthickness=0
        )
        self.timer_listbox.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(list_container, orient="vertical", command=self.timer_listbox.yview)
        sb.pack(side="right", fill="y")
        self.timer_listbox.configure(yscrollcommand=sb.set)
        
        # Populate history
        self.update_timer_ui_list()
        
        # Start clock updates
        self.update_clock_loop()

    def update_clock_loop(self):
        if hasattr(self, 'lbl_timer_clock') and self.lbl_timer_clock.winfo_exists():
            if self.timer_running:
                now = time.time()
                self.timer_elapsed = now - self.timer_start_time
                minutes = int(self.timer_elapsed // 60)
                seconds = int(self.timer_elapsed % 60)
                tenths = int((self.timer_elapsed * 10) % 10)
                self.lbl_timer_clock.configure(text=f"{minutes:02d}:{seconds:02d}.{tenths}")
                self.root.after(100, self.update_clock_loop)

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.timer_start_time = time.time() - self.timer_elapsed
            play_cyberpunk_beep("success")
            if hasattr(self, 'btn_timer_toggle') and self.btn_timer_toggle.winfo_exists():
                self.btn_timer_toggle.configure(text="PAUSAR", command=self.pause_timer)
            self.update_clock_loop()
            
    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.timer_elapsed = time.time() - self.timer_start_time
            play_cyberpunk_beep("click")
            if hasattr(self, 'btn_timer_toggle') and self.btn_timer_toggle.winfo_exists():
                self.btn_timer_toggle.configure(text="INICIAR", command=self.start_timer)
                
    def reset_timer(self):
        self.timer_running = False
        self.timer_elapsed = 0.0
        self.run_count = 0
        self.run_history.clear()
        play_cyberpunk_beep("fail")
        if hasattr(self, 'lbl_timer_clock') and self.lbl_timer_clock.winfo_exists():
            self.lbl_timer_clock.configure(text="00:00.0")
            self.lbl_timer_run.configure(text=f"RUN #1")
            self.btn_timer_toggle.configure(text="INICIAR", command=self.start_timer)
            self.update_timer_ui_list()
            
    def next_run(self):
        if not self.timer_running:
            self.start_timer()
            return
            
        now = time.time()
        dur = now - self.timer_start_time
        
        self.run_count += 1
        minutes = int(dur // 60)
        seconds = int(dur % 60)
        tenths = int((dur * 10) % 10)
        formatted_time = f"{minutes:02d}:{seconds:02d}.{tenths}"
        
        self.run_history.append((self.run_count, dur, formatted_time))
        play_cyberpunk_beep("success")
        
        self.timer_start_time = time.time()
        self.timer_elapsed = 0.0
        
        if hasattr(self, 'lbl_timer_run') and self.lbl_timer_run.winfo_exists():
            self.lbl_timer_run.configure(text=f"RUN #{self.run_count + 1}")
            self.update_timer_ui_list()

    def update_timer_ui_list(self):
        if not hasattr(self, 'timer_listbox') or not self.timer_listbox.winfo_exists():
            return
            
        self.timer_listbox.delete(0, tk.END)
        if not self.run_history:
            self.timer_listbox.insert(tk.END, "Nenhuma run registrada ainda.")
            self.lbl_average.configure(text="Tempo Médio: --:--.-")
            return
            
        total_time = 0.0
        for run_num, dur, f_time in reversed(self.run_history):
            self.timer_listbox.insert(tk.END, f" Run #{run_num:03d}  --->  {f_time}")
            total_time += dur
            
        avg = total_time / len(self.run_history)
        avg_min = int(avg // 60)
        avg_sec = int(avg % 60)
        avg_tenth = int((avg * 10) % 10)
        self.lbl_average.configure(text=f"Tempo Médio: {avg_min:02d}:{avg_sec:02d}.{avg_tenth}")

    # ==================== TAB 6: AUTO CLICKER ====================
    def show_autoclicker_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="AUTO CLICKER / MOUSE MACRO",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        ac_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        ac_frame.place(x=10, y=40, width=390, height=420)
        
        tk.Label(
            ac_frame,
            text="STATUS ATUAL:",
            fg="#8a99ad",
            bg="#12131a",
            font=("Yu Gothic UI", 10, "bold")
        ).place(x=20, y=20)
        
        self.lbl_ac_status = tk.Label(
            ac_frame,
            text="DESATIVADO" if not self.autoclicker_active else "ATIVO",
            fg="#ff2a2a" if not self.autoclicker_active else "#00ff00",
            bg="#12131a",
            font=("Yu Gothic UI", 12, "bold")
        )
        self.lbl_ac_status.place(x=130, y=18)
        
        tk.Label(
            ac_frame,
            text="Intervalo de Clique (ms):",
            fg="#8a99ad",
            bg="#12131a",
            font=("Yu Gothic UI", 9, "bold")
        ).place(x=20, y=70)
        
        self.ac_speed_var = tk.StringVar(value=str(self.app.click_speed))
        self.ac_speed_var.trace_add("write", self.on_click_speed_change)
        
        ac_speed_entry = tk.Entry(
            ac_frame,
            textvariable=self.ac_speed_var,
            bg="#050608",
            fg="#ffffff",
            bd=1,
            relief="solid",
            insertbackground="#ffffff",
            font=("Consolas", 10, "bold"),
            justify="center"
        )
        ac_speed_entry.place(x=210, y=70, width=70, height=22)
        
        tk.Label(
            ac_frame,
            text="Botão do Mouse:",
            fg="#8a99ad",
            bg="#12131a",
            font=("Yu Gothic UI", 9, "bold")
        ).place(x=20, y=110)
        
        self.ac_btn_var = tk.StringVar(value=self.app.click_button)
        
        rb_left = tk.Radiobutton(
            ac_frame,
            text="Esquerdo (Left)",
            variable=self.ac_btn_var,
            value="Left",
            command=self.on_click_button_change,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 9)
        )
        rb_left.place(x=150, y=110)
        
        rb_right = tk.Radiobutton(
            ac_frame,
            text="Direito (Right)",
            variable=self.ac_btn_var,
            value="Right",
            command=self.on_click_button_change,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 9)
        )
        rb_right.place(x=260, y=110)
        
        self.btn_ac_toggle = self.create_flat_button(
            ac_frame,
            "ATIVAR AUTO CLICKER (Alt+C)" if not self.autoclicker_active else "DESATIVAR AUTO CLICKER (Alt+C)",
            self.toggle_autoclicker,
            20, 160, 350, 40
        )
        
        ac_help = (
            "Instruções do Auto Clicker:\n\n"
            "1. Defina o intervalo de cliques em milissegundos (ex: 100ms).\n"
            "2. Escolha qual botão do mouse simular (Esquerdo ou Direito).\n"
            "3. Pressione a tecla de atalho global ALT + C dentro do jogo\n"
            "   para ativar ou desativar o clicker instantaneamente.\n"
            "4. A simulação funciona em segundo plano e injeta eventos\n"
            "   diretamente no hardware scancode do Windows."
        )
        
        lbl_ac_help = tk.Label(
            ac_frame,
            text=ac_help,
            fg="#aaaaaa",
            bg="#050608",
            justify="left",
            font=("Yu Gothic UI", 9),
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )
        lbl_ac_help.place(x=20, y=225, width=350, height=170)

    def on_click_speed_change(self, *args):
        try:
            val = int(self.ac_speed_var.get())
            if val < 5:
                val = 5
            self.app.click_speed = val
        except ValueError:
            pass
            
    def on_click_button_change(self):
        self.app.click_button = self.ac_btn_var.get()
        play_cyberpunk_beep("click")

    def toggle_autoclicker(self):
        self.autoclicker_active = not self.autoclicker_active
        if self.autoclicker_active:
            play_cyberpunk_beep("success")
        else:
            play_cyberpunk_beep("fail")
            
        if hasattr(self, 'lbl_ac_status') and self.lbl_ac_status.winfo_exists():
            self.lbl_ac_status.configure(
                text="ATIVO" if self.autoclicker_active else "DESATIVADO",
                fg="#00ff00" if self.autoclicker_active else "#ff2a2a"
            )
            self.btn_ac_toggle.configure(
                text="DESATIVAR AUTO CLICKER (Alt+C)" if self.autoclicker_active else "ATIVAR AUTO CLICKER (Alt+C)"
            )

    # ==================== TAB 7: SETTINGS ====================
    def show_settings_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="CONFIGURAÇÕES DO HUB",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        ctrl_frame = tk.Frame(self.content_frame, bg="#12131a", bd=1, relief="solid")
        ctrl_frame.place(x=10, y=45, width=390, height=415)
        
        self.topmost_var = tk.BooleanVar(value=self.app.root.attributes("-topmost"))
        cb_topmost = tk.Checkbutton(
            ctrl_frame,
            text="Sempre no Topo (Always on Top)",
            variable=self.topmost_var,
            command=self.update_topmost,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 9, "bold")
        )
        cb_topmost.place(x=15, y=20)
        
        global SOUNDS_ENABLED
        self.sounds_var = tk.BooleanVar(value=SOUNDS_ENABLED)
        cb_sounds = tk.Checkbutton(
            ctrl_frame,
            text="Efeitos Sonoros (Sons/Beeps)",
            variable=self.sounds_var,
            command=self.update_sounds,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 9, "bold")
        )
        cb_sounds.place(x=15, y=60)
        
        global PARTICLES_ENABLED
        self.particles_var = tk.BooleanVar(value=PARTICLES_ENABLED)
        cb_particles = tk.Checkbutton(
            ctrl_frame,
            text="Partículas Flutuantes no HUD (Canvas Particles)",
            variable=self.particles_var,
            command=self.update_particles_setting,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 9, "bold")
        )
        cb_particles.place(x=15, y=100)
        
        tk.Label(
            ctrl_frame,
            text="Opacidade do Hub (Main Transparency):",
            fg="#8a99ad",
            bg="#12131a",
            font=("Yu Gothic UI", 9, "bold")
        ).place(x=18, y=145)
        
        self.opacity_var = tk.DoubleVar(value=self.app.root.attributes("-alpha"))
        slider = tk.Scale(
            ctrl_frame,
            from_=0.15,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.opacity_var,
            command=self.update_opacity,
            bg="#12131a",
            fg="#ffffff",
            troughcolor="#050608",
            activebackground="#ff2a2a",
            highlightthickness=0,
            bd=0
        )
        slider.place(x=18, y=170, width=350)

        help_text = (
            "Dicas de Uso do Kakashi Hub:\n\n"
            "• Use Scroll no HUD Principal para ajustar transparência.\n"
            "• Segure o clique esquerdo e arraste no HUD para movê-lo.\n"
            "• Atalhos rápidos para trocar de filtro:\n"
            "  Alt+1 (Normal)  |  Alt+2 (Elite)  |  Alt+3 (Kakashi)\n"
            "  Alt+4 (MF)      |  Alt+5 (RW All)\n"
            "• Cronômetro de Runs: Pressione Alt+T no jogo para split.\n"
            "• Auto Clicker: Pressione Alt+C no jogo para ligar/desligar."
        )
        
        lbl_help = tk.Label(
            ctrl_frame,
            text=help_text,
            fg="#aaaaaa",
            bg="#050608",
            justify="left",
            font=("Yu Gothic UI", 9),
            bd=1,
            relief="solid",
            padx=10,
            pady=10
        )
        lbl_help.place(x=18, y=240, width=350, height=155)

    def update_topmost(self):
        val = self.topmost_var.get()
        self.app.root.attributes("-topmost", val)
        self.root.attributes("-topmost", val)
        play_cyberpunk_beep("click")
        
    def update_sounds(self):
        global SOUNDS_ENABLED
        SOUNDS_ENABLED = self.sounds_var.get()
        play_cyberpunk_beep("click")
        
    def update_particles_setting(self):
        global PARTICLES_ENABLED
        PARTICLES_ENABLED = self.particles_var.get()
        play_cyberpunk_beep("click")
        
    def update_opacity(self, val):
        self.app.root.attributes("-alpha", float(val))

    def trigger_hp_calibration(self):
        mx, my = get_mouse_pos()
        r, g, b = get_pixel_color(mx, my)
        self.app.hp_pixel_x = mx
        self.app.hp_pixel_y = my
        self.app.hp_pixel_r = r
        self.app.save_current_profile()
        play_cyberpunk_beep("success")
        log_debug(f"HP Calibrated: x={mx}, y={my}, red={r}")
        if hasattr(self, 'lbl_hp_coords') and self.lbl_hp_coords.winfo_exists():
            self.lbl_hp_coords.configure(text=f"Coords: ({mx}, {my}) | Cor R: {r}")

    def trigger_mp_calibration(self):
        mx, my = get_mouse_pos()
        r, g, b = get_pixel_color(mx, my)
        self.app.mp_pixel_x = mx
        self.app.mp_pixel_y = my
        self.app.mp_pixel_b = b
        self.app.save_current_profile()
        play_cyberpunk_beep("success")
        log_debug(f"MP Calibrated: x={mx}, y={my}, blue={b}")
        if hasattr(self, 'lbl_mp_coords') and self.lbl_mp_coords.winfo_exists():
            self.lbl_mp_coords.configure(text=f"Coords: ({mx}, {my}) | Cor B: {b}")

    def trigger_town_calibration(self):
        mx, my = get_mouse_pos()
        r, g, b = get_pixel_color(mx, my)
        self.app.town_pixel_x = mx
        self.app.town_pixel_y = my
        self.app.town_pixel_r = r
        self.app.town_pixel_g = g
        self.app.town_pixel_b = b
        self.app.save_current_profile()
        play_cyberpunk_beep("success")
        log_debug(f"Town Calibrated: x={mx}, y={my}, color=({r},{g},{b})")
        if hasattr(self, 'lbl_town_coords') and self.lbl_town_coords.winfo_exists():
            self.lbl_town_coords.configure(text=f"Coords: ({mx}, {my}) | RGB: ({r},{g},{b})")

    # ==================== TAB 8: AUTO POT ====================
    def show_autopot_tab(self):
        play_cyberpunk_beep("click")
        self.clear_content()
        
        tk.Label(
            self.content_frame,
            text="SISTEMA AUTO POTION (HP & MP)",
            fg="#ffffff",
            bg="#0b0c10",
            font=("Yu Gothic UI", 11, "bold")
        ).place(x=10, y=10)
        
        # Profile Frame
        profile_frame = tk.Frame(self.content_frame, bg="#0b0c10")
        profile_frame.place(x=10, y=35, width=440, height=35)
        
        tk.Label(profile_frame, text="PERFIL ATIVO:", fg="#8a99ad", bg="#0b0c10", font=("Yu Gothic UI", 9, "bold")).place(x=0, y=5)
        
        def set_profile(prof_name):
            play_cyberpunk_beep("success")
            self.app.load_profile_data(prof_name)
            self.show_autopot_tab()
            
        profiles = ["PvP", "MF", "Rush"]
        px = 100
        for p in profiles:
            bg_color = "#330000" if self.app.current_profile == p else "#1c1d24"
            fg_color = "#ff2a2a" if self.app.current_profile == p else "#aaaaaa"
            btn = tk.Button(
                profile_frame,
                text=p,
                command=lambda name=p: set_profile(name),
                bg=bg_color,
                fg=fg_color,
                activebackground="#330000",
                activeforeground="#ff2a2a",
                bd=1,
                relief="solid",
                font=("Consolas", 9, "bold")
            )
            btn.place(x=px, y=2, width=55, height=22)
            px += 65

        # HP Frame
        hp_frame = tk.LabelFrame(
            self.content_frame,
            text=" CONFIGURAÇÃO DE VIDA (HP) ",
            fg="#ff2a2a",
            bg="#12131a",
            bd=1,
            relief="solid",
            font=("Yu Gothic UI", 9, "bold")
        )
        hp_frame.place(x=10, y=75, width=440, height=140)
        
        self.autopot_hp_var = tk.BooleanVar(value=self.app.autopot_hp_enabled)
        cb_hp = tk.Checkbutton(
            hp_frame,
            text="Ativar Auto Potion HP",
            variable=self.autopot_hp_var,
            command=self.update_hp_autopot,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 9, "bold")
        )
        cb_hp.place(x=10, y=10)
        
        tk.Label(hp_frame, text="Tecla de Pot:", fg="#8a99ad", bg="#12131a", font=("Yu Gothic UI", 9)).place(x=10, y=45)
        self.hp_key_var = tk.StringVar(value=self.app.autopot_hp_key)
        self.hp_key_var.trace_add("write", self.on_hp_key_change)
        entry_hp_key = tk.Entry(hp_frame, textvariable=self.hp_key_var, bg="#050608", fg="#ffffff", bd=1, relief="solid", justify="center", font=("Consolas", 9, "bold"))
        entry_hp_key.place(x=90, y=45, width=30, height=20)
        
        tk.Label(hp_frame, text="Cooldown (s):", fg="#8a99ad", bg="#12131a", font=("Yu Gothic UI", 9)).place(x=140, y=45)
        self.hp_coold_var = tk.StringVar(value=str(self.app.autopot_hp_cooldown))
        self.hp_coold_var.trace_add("write", self.on_hp_coold_change)
        entry_hp_coold = tk.Entry(hp_frame, textvariable=self.hp_coold_var, bg="#050608", fg="#ffffff", bd=1, relief="solid", justify="center", font=("Consolas", 9, "bold"))
        entry_hp_coold.place(x=220, y=45, width=40, height=20)
        
        hp_coord_text = f"Coords: ({self.app.hp_pixel_x}, {self.app.hp_pixel_y}) | Cor R: {self.app.hp_pixel_r}" if self.app.hp_pixel_x > 0 else "NÃO CALIBRADO"
        self.lbl_hp_coords = tk.Label(hp_frame, text=hp_coord_text, fg="#ffffff", bg="#12131a", font=("Consolas", 9))
        self.lbl_hp_coords.place(x=10, y=80)
        
        self.create_flat_button(
            hp_frame,
            "CALIBRAR HP (F7)",
            self.trigger_hp_calibration,
            10, 105, 410, 22
        )
        
        # MP Frame
        mp_frame = tk.LabelFrame(
            self.content_frame,
            text=" CONFIGURAÇÃO DE MANA (MP) ",
            fg="#2a8cff",
            bg="#12131a",
            bd=1,
            relief="solid",
            font=("Yu Gothic UI", 9, "bold")
        )
        mp_frame.place(x=10, y=225, width=440, height=140)
        
        self.autopot_mp_var = tk.BooleanVar(value=self.app.autopot_mp_enabled)
        cb_mp = tk.Checkbutton(
            mp_frame,
            text="Ativar Auto Potion MP",
            variable=self.autopot_mp_var,
            command=self.update_mp_autopot,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 9, "bold")
        )
        cb_mp.place(x=10, y=10)
        
        tk.Label(mp_frame, text="Tecla de Pot:", fg="#8a99ad", bg="#12131a", font=("Yu Gothic UI", 9)).place(x=10, y=45)
        self.mp_key_var = tk.StringVar(value=self.app.autopot_mp_key)
        self.mp_key_var.trace_add("write", self.on_mp_key_change)
        entry_mp_key = tk.Entry(mp_frame, textvariable=self.mp_key_var, bg="#050608", fg="#ffffff", bd=1, relief="solid", justify="center", font=("Consolas", 9, "bold"))
        entry_mp_key.place(x=90, y=45, width=30, height=20)
        
        tk.Label(mp_frame, text="Cooldown (s):", fg="#8a99ad", bg="#12131a", font=("Yu Gothic UI", 9)).place(x=140, y=45)
        self.mp_coold_var = tk.StringVar(value=str(self.app.autopot_mp_cooldown))
        self.mp_coold_var.trace_add("write", self.on_mp_coold_change)
        entry_mp_coold = tk.Entry(mp_frame, textvariable=self.mp_coold_var, bg="#050608", fg="#ffffff", bd=1, relief="solid", justify="center", font=("Consolas", 9, "bold"))
        entry_mp_coold.place(x=220, y=45, width=40, height=20)
        
        mp_coord_text = f"Coords: ({self.app.mp_pixel_x}, {self.app.mp_pixel_y}) | Cor B: {self.app.mp_pixel_b}" if self.app.mp_pixel_x > 0 else "NÃO CALIBRADO"
        self.lbl_mp_coords = tk.Label(mp_frame, text=mp_coord_text, fg="#ffffff", bg="#12131a", font=("Consolas", 9))
        self.lbl_mp_coords.place(x=10, y=80)
        
        self.create_flat_button(
            mp_frame,
            "CALIBRAR MP (F8)",
            self.trigger_mp_calibration,
            10, 105, 410, 22
        )
        
        # Advanced Frame
        adv_frame = tk.LabelFrame(
            self.content_frame,
            text=" SISTEMA ASSISTENTE INTELIGENTE & CALIBRAÇÕES ",
            fg="#ee00ff",
            bg="#12131a",
            bd=1,
            relief="solid",
            font=("Yu Gothic UI", 9, "bold")
        )
        adv_frame.place(x=10, y=375, width=440, height=125)
        
        # 1. Rejuv Option
        self.rejuv_enabled_var = tk.BooleanVar(value=self.app.auto_rejuv_enabled)
        def toggle_rejuv():
            self.app.auto_rejuv_enabled = self.rejuv_enabled_var.get()
            play_cyberpunk_beep("click")
        cb_rejuv = tk.Checkbutton(
            adv_frame,
            text="Auto Rejuv",
            variable=self.rejuv_enabled_var,
            command=toggle_rejuv,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 8, "bold")
        )
        cb_rejuv.place(x=10, y=10)
        
        tk.Label(adv_frame, text="Tecla:", fg="#8a99ad", bg="#12131a", font=("Yu Gothic UI", 8)).place(x=100, y=12)
        self.rejuv_key_var = tk.StringVar(value=self.app.rejuv_key)
        def on_rejuv_key_change(*args):
            val = self.rejuv_key_var.get()
            if val: self.app.rejuv_key = val[0]
        self.rejuv_key_var.trace_add("write", on_rejuv_key_change)
        entry_rejuv_key = tk.Entry(adv_frame, textvariable=self.rejuv_key_var, bg="#050608", fg="#ffffff", bd=1, relief="solid", justify="center", font=("Consolas", 8, "bold"))
        entry_rejuv_key.place(x=135, y=12, width=20, height=18)
        
        tk.Label(adv_frame, text="Trigger %:", fg="#8a99ad", bg="#12131a", font=("Yu Gothic UI", 8)).place(x=160, y=12)
        self.rejuv_pct_var = tk.StringVar(value=str(self.app.rejuv_trigger_pct))
        def on_rejuv_pct_change(*args):
            val = self.rejuv_pct_var.get()
            if val.isdigit(): self.app.rejuv_trigger_pct = int(val)
        self.rejuv_pct_var.trace_add("write", on_rejuv_pct_change)
        entry_rejuv_pct = tk.Entry(adv_frame, textvariable=self.rejuv_pct_var, bg="#050608", fg="#ffffff", bd=1, relief="solid", justify="center", font=("Consolas", 8, "bold"))
        entry_rejuv_pct.place(x=215, y=12, width=25, height=18)
        
        # 2. ESC Option
        self.esc_enabled_var = tk.BooleanVar(value=self.app.auto_esc_enabled)
        def toggle_esc():
            self.app.auto_esc_enabled = self.esc_enabled_var.get()
            play_cyberpunk_beep("click")
        cb_esc = tk.Checkbutton(
            adv_frame,
            text="Auto ESC",
            variable=self.esc_enabled_var,
            command=toggle_esc,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 8, "bold")
        )
        cb_esc.place(x=255, y=10)
        
        tk.Label(adv_frame, text="HP %:", fg="#8a99ad", bg="#12131a", font=("Yu Gothic UI", 8)).place(x=330, y=12)
        self.esc_pct_var = tk.StringVar(value=str(self.app.esc_trigger_pct))
        def on_esc_pct_change(*args):
            val = self.esc_pct_var.get()
            if val.isdigit(): self.app.esc_trigger_pct = int(val)
        self.esc_pct_var.trace_add("write", on_esc_pct_change)
        entry_esc_pct = tk.Entry(adv_frame, textvariable=self.esc_pct_var, bg="#050608", fg="#ffffff", bd=1, relief="solid", justify="center", font=("Consolas", 8, "bold"))
        entry_esc_pct.place(x=365, y=12, width=25, height=18)
        
        # 3. Town Calibration Option
        self.town_enabled_var = tk.BooleanVar(value=self.app.town_pixel_enabled)
        def toggle_town():
            self.app.town_pixel_enabled = self.town_enabled_var.get()
            play_cyberpunk_beep("click")
        cb_town = tk.Checkbutton(
            adv_frame,
            text="Ativar Estado de Cidade (Detecção)",
            variable=self.town_enabled_var,
            command=toggle_town,
            bg="#12131a",
            fg="#8a99ad",
            selectcolor="#050608",
            activebackground="#12131a",
            activeforeground="#ffffff",
            font=("Yu Gothic UI", 8, "bold")
        )
        cb_town.place(x=10, y=42)
        
        town_coord_text = f"Town: ({self.app.town_pixel_x}, {self.app.town_pixel_y}) | RGB: ({self.app.town_pixel_r}, {self.app.town_pixel_g}, {self.app.town_pixel_b})" if self.app.town_pixel_x > 0 else "Town: NÃO CALIBRADO"
        self.lbl_town_coords = tk.Label(adv_frame, text=town_coord_text, fg="#ffffff", bg="#12131a", font=("Consolas", 8))
        self.lbl_town_coords.place(x=10, y=67)
        
        self.create_flat_button(
            adv_frame,
            "CALIBRAR CIDADE (F9)",
            self.trigger_town_calibration,
            10, 92, 410, 20
        )
        
        # Help Frame
        help_frame = tk.Frame(self.content_frame, bg="#050608", bd=1, relief="solid")
        help_frame.place(x=10, y=508, width=440, height=45)
        
        help_lbl = (
            "1. HP/MP: Cursor na orbe + F7/F8 para calibrar cor/posição.\n"
            "2. Cidade: Cursor em elemento único de HUD da Cidade (ex: Portal/Waypoint) + F9.\n"
            "3. O Auto Pot age quando as cores de HP/MP caem abaixo dos limites definidos."
        )
        tk.Label(
            help_frame,
            text=help_lbl,
            fg="#aaaaaa",
            bg="#050608",
            justify="left",
            font=("Yu Gothic UI", 7)
        ).place(x=10, y=2)

    def update_hp_autopot(self):
        self.app.autopot_hp_enabled = self.autopot_hp_var.get()
        self.app.save_current_profile()
        play_cyberpunk_beep("click")
        
    def update_mp_autopot(self):
        self.app.autopot_mp_enabled = self.autopot_mp_var.get()
        self.app.save_current_profile()
        play_cyberpunk_beep("click")
        
    def on_hp_key_change(self, *args):
        val = self.hp_key_var.get()
        if val:
            self.app.autopot_hp_key = val[0]
            self.app.save_current_profile()
            
    def on_mp_key_change(self, *args):
        val = self.mp_key_var.get()
        if val:
            self.app.autopot_mp_key = val[0]
            self.app.save_current_profile()
            
    def on_hp_coold_change(self, *args):
        try:
            val = float(self.hp_coold_var.get())
            if val < 0.1:
                val = 0.1
            self.app.autopot_hp_cooldown = val
            self.app.save_current_profile()
        except ValueError:
            pass
            
    def on_mp_coold_change(self, *args):
        try:
            val = float(self.mp_coold_var.get())
            if val < 0.1:
                val = 0.1
            self.app.autopot_mp_cooldown = val
            self.app.save_current_profile()
        except ValueError:
            pass



    def sync_from_app(self):
        if hasattr(self, 'autopot_hp_var'): self.autopot_hp_var.set(self.app.autopot_hp_enabled)
        if hasattr(self, 'autopot_mp_var'): self.autopot_mp_var.set(self.app.autopot_mp_enabled)
        if hasattr(self, 'hp_key_var'): self.hp_key_var.set(self.app.autopot_hp_key)
        if hasattr(self, 'mp_key_var'): self.mp_key_var.set(self.app.autopot_mp_key)
        if hasattr(self, 'hp_coold_var'): self.hp_coold_var.set(str(self.app.autopot_hp_cooldown))
        if hasattr(self, 'mp_coold_var'): self.mp_coold_var.set(str(self.app.autopot_mp_cooldown))
        
        if hasattr(self, 'lbl_hp_coords'):
            hp_coord_text = f"Coords: ({self.app.hp_pixel_x}, {self.app.hp_pixel_y}) | Cor R: {self.app.hp_pixel_r}" if self.app.hp_pixel_x > 0 else "NÃO CALIBRADO"
            self.lbl_hp_coords.configure(text=hp_coord_text)
        if hasattr(self, 'lbl_mp_coords'):
            mp_coord_text = f"Coords: ({self.app.mp_pixel_x}, {self.app.mp_pixel_y}) | Cor B: {self.app.mp_pixel_b}" if self.app.mp_pixel_x > 0 else "NÃO CALIBRADO"
            self.lbl_mp_coords.configure(text=mp_coord_text)
            
        if hasattr(self, 'rejuv_enabled_var'): self.rejuv_enabled_var.set(self.app.auto_rejuv_enabled)
        if hasattr(self, 'rejuv_key_var'): self.rejuv_key_var.set(self.app.rejuv_key)
        if hasattr(self, 'rejuv_pct_var'): self.rejuv_pct_var.set(str(self.app.rejuv_trigger_pct))
        if hasattr(self, 'esc_enabled_var'): self.esc_enabled_var.set(self.app.auto_esc_enabled)
        if hasattr(self, 'esc_pct_var'): self.esc_pct_var.set(str(self.app.esc_trigger_pct))
        if hasattr(self, 'town_enabled_var'): self.town_enabled_var.set(self.app.town_pixel_enabled)
        
        if hasattr(self, 'lbl_town_coords'):
            town_coord_text = f"Town: ({self.app.town_pixel_x}, {self.app.town_pixel_y}) | RGB: ({self.app.town_pixel_r}, {self.app.town_pixel_g}, {self.app.town_pixel_b})" if self.app.town_pixel_x > 0 else "Town: NÃO CALIBRADO"
            self.lbl_town_coords.configure(text=town_coord_text)

# ==========================================
# MAIN APP HUB CONTROLLER
# ==========================================
class KakashiHubApp:
    def __init__(self):
        log_debug("Initializing KakashiHubApp...")
        # 1. Download images/icons if missing
        if not os.path.exists(img_path):
            download_file(img_url, img_path)
        if not os.path.exists(ico_path):
            download_file(ico_url, ico_path)
        if not os.path.exists(fundo_path):
            download_file(fundo_url, fundo_path)
            
        # 2. Run Loader Splash Screen
        LoaderWindow()
        
        # 3. Create Main Window
        log_debug("Creating main window UI...")
        self.root = tk.Tk()
        self.root.title("BH HUB")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9) # 230/255 transparency
        
        try:
            self.root.iconbitmap(ico_path)
        except Exception as e:
            log_debug(f"Error setting icon: {e}")
            
        # Placement (Top Right Corner) - Extended height from 250 to 280 to fit update button
        w, h = 200, 280
        work_left, work_top, work_right, work_bottom = get_work_area()
        x_pos = work_right - 210
        y_pos = work_top + 5
        self.root.geometry(f"{w}x{h}+{x_pos}+{y_pos}")
        log_debug(f"Main window geometry set: {w}x{h}+{x_pos}+{y_pos}")
        
        # Background canvas for double-buffered animation
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bind MouseWheel scroll for dynamic transparency adjustment
        self.canvas.bind("<MouseWheel>", self.adjust_opacity)
        
        # Main background image
        self.bg_photo = None
        if os.path.exists(img_path):
            try:
                bg_img = Image.open(img_path).resize((w, h))
                self.bg_photo = ImageTk.PhotoImage(bg_img)
                self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
                log_debug("Main background image loaded.")
            except Exception as e:
                log_debug(f"Main kakashi.jpg load error: {e}")
                
        # Drag support variables
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.toolbox_instance = None
        self.click_button = "Left"
        self.click_speed = 100
        
        # Session Telemetry
        self.session_runs = 0
        self.session_hp_pots = 0
        self.session_mp_pots = 0
        self.session_near_deaths = 0
        self.session_deaths = 0
        self.session_start_time = time.time()
        self.run_start_time = 0.0
        self.active_combat_time = 0.0
        self.run_active_duration = 0.0
        self.is_in_run = False
        
        # State detection
        self.game_state = "DESCONHECIDO" # "CARREGANDO", "CIDADE", "COMBATE", "MORTO"
        self.last_hp_sample_time = 0.0
        self.hp_history = [] # list of (timestamp, red_value)
        self.last_action_time = time.time()
        
        # Town pixel calibration
        self.town_pixel_x = 0
        self.town_pixel_y = 0
        self.town_pixel_r = 0
        self.town_pixel_g = 0
        self.town_pixel_b = 0
        self.town_pixel_enabled = False
        
        # Advanced actions
        self.auto_rejuv_enabled = False
        self.rejuv_key = "3"
        self.rejuv_trigger_pct = 35
        self.auto_esc_enabled = False
        self.esc_trigger_pct = 10
        self.streamer_mode = False
        
        # Alert Overlay
        self.overlay_window = None
        self.active_alerts = []
        
        # Auto Pot configuration state (will be overwritten by profile load)
        self.autopot_hp_enabled = False
        self.autopot_mp_enabled = False
        self.autopot_hp_key = "1"
        self.autopot_mp_key = "2"
        self.autopot_hp_cooldown = 2.0
        self.autopot_mp_cooldown = 2.0
        
        # Calibration state
        self.hp_pixel_x = 0
        self.hp_pixel_y = 0
        self.hp_pixel_r = 0
        self.mp_pixel_x = 0
        self.mp_pixel_y = 0
        self.mp_pixel_b = 0
        
        # Load persistent configuration
        self.config_data = load_config()
        self.current_profile = self.config_data.get("current_profile", "PvP")
        self.load_profile_data(self.current_profile)
        
        # Start AutoPot background loop thread
        threading.Thread(target=self.autopot_loop, daemon=True).start()
        
        # Drag and drop events
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        
        # Neon Border Lines (Adjusted bottom border to Y=280)
        self.top_border = self.canvas.create_rectangle(0, 0, 200, 2, fill="#550000", width=0)
        self.bot_border = self.canvas.create_rectangle(0, 278, 200, 280, fill="#220000", width=0)
        self.left_border = self.canvas.create_rectangle(0, 0, 2, 280, fill="#330000", width=0)
        self.right_border = self.canvas.create_rectangle(198, 0, 200, 280, fill="#110000", width=0)
        
        # Title & Status labels
        self.title_text = self.canvas.create_text(10, 15, text="Kakashi HUB", fill="#ffffff", font=("Yu Gothic UI", 10, "bold"), anchor="w")
        self.status_text = self.canvas.create_text(100, 38, text="[NENHUM]", fill="#aaaaaa", font=("Yu Gothic UI", 9, "bold"), anchor="center")
        
        # Header Controls
        self.btn_min = self.canvas.create_text(150, 12, text="_", fill="#ffffff", font=("Yu Gothic UI", 10, "bold"), anchor="center")
        self.btn_close = self.canvas.create_text(175, 12, text="X", fill="#ffffff", font=("Yu Gothic UI", 10, "bold"), anchor="center")
        
        self.canvas.tag_bind(self.btn_min, "<Button-1>", self.toggle_minimize)
        self.canvas.tag_bind(self.btn_close, "<Button-1>", self.close_app)
        
        # Configuration/Loot Filter Buttons (using 3D canvas buttons)
        self.active_config = ""
        self.btn_normal = self.create_canvas_3d_button(72, "NORMAL", "BH_normal.cfg", lambda e: self.swap_filter("BH_normal.cfg", "NORMAL"))
        self.btn_elite = self.create_canvas_3d_button(102, "ELITE", "BH_elite.cfg", lambda e: self.swap_filter("BH_elite.cfg", "ELITE"))
        self.btn_rw = self.create_canvas_3d_button(132, "KAKASHI", "BH_rw.cfg", lambda e: self.swap_filter("BH_rw.cfg", "KAKASHI"))
        self.btn_mf = self.create_canvas_3d_button(162, "MF", "BH_mf.cfg", lambda e: self.swap_filter("BH_mf.cfg", "MF"))
        self.btn_rwall = self.create_canvas_3d_button(192, "RW ALL", "BH_rwall.cfg", lambda e: self.swap_filter("BH_rwall.cfg", "RW ALL"))
        self.btn_builds = self.create_canvas_3d_button(222, "TOOLBOX", "", lambda e: self.show_toolbox())
        self.btn_update = self.create_canvas_3d_button(252, "ATUALIZAR", "", lambda e: self.force_update_configs())
        
        self.filter_buttons = {
            "BH_normal.cfg": self.btn_normal,
            "BH_elite.cfg": self.btn_elite,
            "BH_rw.cfg": self.btn_rw,
            "BH_mf.cfg": self.btn_mf,
            "BH_rwall.cfg": self.btn_rwall
        }
        
        # Minimization state
        self.is_minimized = False
        
        # Pulse animation state
        self.pulse_val = 120
        self.pulse_dir = 5
        
        # Neon pulsing border state
        self.neon_pulse = 120
        self.neon_dir = 5
        
        # Canvas Particle System state
        self.particles = []
        
        # Start game-monitoring, animations, particles
        self.animate_ui()
        self.animate_neon()
        self.update_particles()
        self.monitor_game()
        
        # Start Background Global Hotkey Listener (Alt+1 to Alt+5)
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        
        log_debug("Entering main window mainloop...")
        self.root.mainloop()
        log_debug("Main window mainloop ended.")
        
    def create_canvas_3d_button(self, y_center, text, config_name, click_cmd):
        # Premium 3D dark button drawn on canvas
        x1, y1 = 30, y_center - 12
        x2, y2 = 170, y_center + 12
        
        # 1. Main background (pitch dark)
        bg_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="#12131a", outline="#000000", width=1)
        
        # 2. Bevel highlights (light source at top-left, shadow at bottom-right)
        hl_id = self.canvas.create_line(x1+1, y1+1, x2-1, y1+1, fill="#383b4d")
        hl_side_id = self.canvas.create_line(x1+1, y1+1, x1+1, y2-1, fill="#383b4d")
        
        sh_id = self.canvas.create_line(x1+1, y2-1, x2-1, y2-1, fill="#050608")
        sh_side_id = self.canvas.create_line(x2-1, y1+1, x2-1, y2-1, fill="#050608")
        
        # 3. Label text
        text_id = self.canvas.create_text(100, y_center, text=text, fill="#aaaaaa", font=("Yu Gothic UI", 9, "bold"), anchor="center")
        
        # Helper to dynamically update canvas styles for tactile visual feedback
        def set_state(state):
            if state == 'active':
                self.canvas.itemconfig(bg_id, fill="#2b0000", outline="#ff0000")
                self.canvas.itemconfig(text_id, fill="#ff2a2a")
                # Flip 3D bevel to "pressed down" inset state
                self.canvas.itemconfig(hl_id, fill="#050608")
                self.canvas.itemconfig(hl_side_id, fill="#050608")
                self.canvas.itemconfig(sh_id, fill="#550000")
                self.canvas.itemconfig(sh_side_id, fill="#550000")
            elif state == 'hover':
                self.canvas.itemconfig(bg_id, fill="#1c1d29", outline="#ff2a2a")
                self.canvas.itemconfig(text_id, fill="#ffffff")
                # Brighten bevel edges for hover glow
                self.canvas.itemconfig(hl_id, fill="#4c516d")
                self.canvas.itemconfig(hl_side_id, fill="#4c516d")
                self.canvas.itemconfig(sh_id, fill="#0a0c10")
                self.canvas.itemconfig(sh_side_id, fill="#0a0c10")
            else: # normal
                self.canvas.itemconfig(bg_id, fill="#12131a", outline="#000000")
                self.canvas.itemconfig(text_id, fill="#aaaaaa")
                self.canvas.itemconfig(hl_id, fill="#383b4d")
                self.canvas.itemconfig(hl_side_id, fill="#383b4d")
                self.canvas.itemconfig(sh_id, fill="#050608")
                self.canvas.itemconfig(sh_side_id, fill="#050608")
                
        group = {"bg": bg_id, "hl": hl_id, "hl_s": hl_side_id, "sh": sh_id, "sh_s": sh_side_id, "text": text_id, "set_state": set_state}
        
        def on_enter(e):
            if config_name == "" or self.active_config != config_name:
                set_state('hover')
        def on_leave(e):
            if config_name == "" or self.active_config != config_name:
                set_state('normal')
                
        # Bind events to all canvas parts of this 3D button
        for element_id in [bg_id, hl_id, hl_side_id, sh_id, sh_side_id, text_id]:
            self.canvas.tag_bind(element_id, "<Enter>", on_enter)
            self.canvas.tag_bind(element_id, "<Leave>", on_leave)
            self.canvas.tag_bind(element_id, "<Button-1>", click_cmd)
            
        return group

    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        
    def do_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_start_x
        y = self.root.winfo_y() + event.y - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")
        
    def toggle_minimize(self, event=None):
        if not self.is_minimized:
            self.root.geometry("200x25")
            self.is_minimized = True
            log_debug("Main window minimized.")
        else:
            self.root.geometry("200x280") # Restore to height 280
            self.is_minimized = False
            log_debug("Main window restored.")
            
    def close_app(self, event=None):
        log_debug("Closing application. Terminating game processes...")
        # Terminate game process PrimeDiablo.exe if it's running
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == game_exe.lower():
                    log_debug(f"Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()
            except Exception as e:
                log_debug(f"Error terminating game process: {e}")
        log_debug("Process termination sequence complete. Exiting python script.")
        sys.exit(0)
        
    def load_profile_data(self, profile_name):
        log_debug(f"Loading profile data: {profile_name}")
        prof = self.config_data["profiles"].get(profile_name, DEFAULT_PROFILE.copy())
        
        self.autopot_hp_enabled = prof.get("autopot_hp_enabled", False)
        self.autopot_mp_enabled = prof.get("autopot_mp_enabled", False)
        self.autopot_hp_key = prof.get("autopot_hp_key", "1")
        self.autopot_mp_key = prof.get("autopot_mp_key", "2")
        self.autopot_hp_cooldown = prof.get("autopot_hp_cooldown", 2.0)
        self.autopot_mp_cooldown = prof.get("autopot_mp_cooldown", 2.0)
        
        self.hp_pixel_x = prof.get("hp_pixel_x", 0)
        self.hp_pixel_y = prof.get("hp_pixel_y", 0)
        self.hp_pixel_r = prof.get("hp_pixel_r", 0)
        self.mp_pixel_x = prof.get("mp_pixel_x", 0)
        self.mp_pixel_y = prof.get("mp_pixel_y", 0)
        self.mp_pixel_b = prof.get("mp_pixel_b", 0)
        
        self.click_speed = prof.get("click_speed", 100)
        self.click_button = prof.get("click_button", "Left")
        
        self.town_pixel_x = prof.get("town_pixel_x", 0)
        self.town_pixel_y = prof.get("town_pixel_y", 0)
        self.town_pixel_r = prof.get("town_pixel_r", 0)
        self.town_pixel_g = prof.get("town_pixel_g", 0)
        self.town_pixel_b = prof.get("town_pixel_b", 0)
        self.town_pixel_enabled = prof.get("town_pixel_enabled", False)
        
        self.auto_rejuv_enabled = prof.get("auto_rejuv_enabled", False)
        self.rejuv_key = prof.get("rejuv_key", "3")
        self.rejuv_trigger_pct = prof.get("rejuv_trigger_pct", 35)
        self.auto_esc_enabled = prof.get("auto_esc_enabled", False)
        self.esc_trigger_pct = prof.get("esc_trigger_pct", 10)
        self.streamer_mode = prof.get("streamer_mode", False)
        
        if self.streamer_mode:
            self.enable_streamer_mode()
        else:
            self.disable_streamer_mode()
        
        if self.toolbox_instance and tk.Toplevel.winfo_exists(self.toolbox_instance.root):
            self.toolbox_instance.sync_from_app()

    def save_current_profile(self):
        log_debug(f"Saving current profile: {self.current_profile}")
        if self.current_profile not in self.config_data["profiles"]:
            self.config_data["profiles"][self.current_profile] = {}
        prof = self.config_data["profiles"][self.current_profile]
        
        prof["autopot_hp_enabled"] = self.autopot_hp_enabled
        prof["autopot_mp_enabled"] = self.autopot_mp_enabled
        prof["autopot_hp_key"] = self.autopot_hp_key
        prof["autopot_mp_key"] = self.autopot_mp_key
        prof["autopot_hp_cooldown"] = self.autopot_hp_cooldown
        prof["autopot_mp_cooldown"] = self.autopot_mp_cooldown
        
        prof["hp_pixel_x"] = self.hp_pixel_x
        prof["hp_pixel_y"] = self.hp_pixel_y
        prof["hp_pixel_r"] = self.hp_pixel_r
        prof["mp_pixel_x"] = self.mp_pixel_x
        prof["mp_pixel_y"] = self.mp_pixel_y
        prof["mp_pixel_b"] = self.mp_pixel_b
        
        prof["click_speed"] = self.click_speed
        prof["click_button"] = self.click_button
        
        prof["town_pixel_x"] = self.town_pixel_x
        prof["town_pixel_y"] = self.town_pixel_y
        prof["town_pixel_r"] = self.town_pixel_r
        prof["town_pixel_g"] = self.town_pixel_g
        prof["town_pixel_b"] = self.town_pixel_b
        prof["town_pixel_enabled"] = self.town_pixel_enabled
        
        prof["auto_rejuv_enabled"] = self.auto_rejuv_enabled
        prof["rejuv_key"] = self.rejuv_key
        prof["rejuv_trigger_pct"] = self.rejuv_trigger_pct
        prof["auto_esc_enabled"] = self.auto_esc_enabled
        prof["esc_trigger_pct"] = self.esc_trigger_pct
        prof["streamer_mode"] = self.streamer_mode
        
        self.config_data["current_profile"] = self.current_profile
        save_config(self.config_data)

    def enable_streamer_mode(self):
        self.streamer_mode = True
        self.root.withdraw()
        if not self.overlay_window:
            self.overlay_window = OverlayWindow(self)
        self.overlay_window.set_locked(True)
        log_debug("Streamer Mode enabled. HUD hidden, click-through overlay active.")

    def disable_streamer_mode(self):
        self.streamer_mode = False
        self.root.deiconify()
        if self.overlay_window:
            self.overlay_window.root.destroy()
            self.overlay_window = None
        log_debug("Streamer Mode disabled. HUD restored, overlay destroyed.")
        
    def toggle_streamer_mode(self, event=None):
        if self.streamer_mode:
            self.disable_streamer_mode()
            play_cyberpunk_beep("fail")
        else:
            self.enable_streamer_mode()
            play_cyberpunk_beep("success")
        self.save_current_profile()

    # Scrollwheel Opacity adjustment handler
    def adjust_opacity(self, event):
        current_alpha = self.root.attributes("-alpha")
        # Scroll up event.delta > 0 increases opacity, scroll down decreases
        delta = 0.05 if event.delta > 0 else -0.05
        new_alpha = max(0.15, min(1.0, current_alpha + delta))
        self.root.attributes("-alpha", new_alpha)
        
        # Display opacity feedback temporarily on status text label
        pct = int(new_alpha * 100)
        self.canvas.itemconfig(self.status_text, text=f"OPACIDADE: {pct}%")
        
        # Restore normal label status after 1.5s
        active_lbl = "[NENHUM]"
        if self.active_config:
            # find label name
            for name, btn in self.filter_buttons.items():
                if name == self.active_config:
                    # extract label text
                    active_lbl = self.canvas.itemcget(btn["text"], "text")
                    break
        self.root.after(1500, lambda: self.restore_status_text(f"[{active_lbl}]"))
        
    def restore_status_text(self, text):
        curr_txt = self.canvas.itemcget(self.status_text, "text")
        if "OPACIDADE" in curr_txt:
            self.canvas.itemconfig(self.status_text, text=text)

    # Animations
    def animate_ui(self):
        if self.is_minimized:
            self.root.after(80, self.animate_ui)
            return
            
        self.pulse_val += self.pulse_dir
        if self.pulse_val >= 255:
            self.pulse_val = 255
            self.pulse_dir = -5
        elif self.pulse_val <= 120:
            self.pulse_val = 120
            self.pulse_dir = 5
            
        color_hex = f"#{self.pulse_val:02x}0000"
        self.canvas.itemconfig(self.title_text, fill=color_hex)
        self.root.after(80, self.animate_ui)
        
    def animate_neon(self):
        if self.is_minimized:
            self.root.after(60, self.animate_neon)
            return
            
        self.neon_pulse += self.neon_dir
        if self.neon_pulse >= 255:
            self.neon_pulse = 255
            self.neon_dir = -5
        elif self.neon_pulse <= 80:
            self.neon_pulse = 80
            self.neon_dir = 5
            
        color_hex = f"#{self.neon_pulse:02x}0000"
        self.canvas.itemconfig(self.top_border, fill=color_hex, outline=color_hex)
        self.canvas.itemconfig(self.bot_border, fill=color_hex, outline=color_hex)
        self.root.after(60, self.animate_neon)
        
    def update_particles(self):
        if not PARTICLES_ENABLED:
            for p in self.particles:
                self.canvas.delete(p["id"])
            self.particles.clear()
            self.root.after(200, self.update_particles)
            return

        if self.is_minimized:
            self.root.after(100, self.update_particles)
            return
            
        # Spawn new particle (Adjusted base coordinates for height 280)
        px = random.randint(10, 180)
        p_id = self.canvas.create_oval(px, 250, px+3, 253, fill="#ff0000", outline="#ff0000")
        self.particles.append({"id": p_id, "x": px, "y": 250, "life": 255})
        
        # Update particles
        to_remove = []
        for p in self.particles:
            p["y"] -= 4
            p["life"] -= 15
            if p["life"] <= 0:
                self.canvas.delete(p["id"])
                to_remove.append(p)
            else:
                self.canvas.coords(p["id"], p["x"], p["y"], p["x"]+3, p["y"]+3)
                color_hex = f"#{p['life']:02x}0000"
                self.canvas.itemconfig(p["id"], fill=color_hex, outline=color_hex)
                
        for p in to_remove:
            if p in self.particles:
                self.particles.remove(p)
                
        self.root.after(100, self.update_particles)
        
    def monitor_game(self):
        self.root.after(2000, self.monitor_game)
        
    # Swap Configuration Filters
    def swap_filter(self, config_filename, status_label):
        log_debug(f"Swapping filter config: {config_filename} -> status: {status_label}")
        source = os.path.join(base_path, config_filename)
        dest = os.path.join(base_path, "BH.cfg")
        
        try:
            shutil.copy2(source, dest)
            log_debug("Configuration file copied.")
        except Exception as e:
            log_debug(f"Error copying config file: {e}")
            
        time.sleep(0.15)
        
        # Activate compatible game window (supports multiple typical game executables)
        log_debug("Activating Game window...")
        activated = activate_window_by_process_name(["Game.exe", "D2R.exe", "game.exe", "PrimeDiablo.exe"])
        if activated:
            log_debug("Game window activated. Injecting key combination.")
            time.sleep(0.1)
            # Send Alt+R
            send_alt_r()
        else:
            log_debug("Game window NOT found or not active.")
            
        # Update active config state and update colors
        self.active_config = config_filename
        for cfg, btn_group in self.filter_buttons.items():
            if cfg == config_filename:
                # Highlight active filter in neon-red
                btn_group["set_state"]('active')
            else:
                # Restore others to gray
                btn_group["set_state"]('normal')
                
        # Update Status Text in Canvas
        self.canvas.itemconfig(self.status_text, text=f"[{status_label}]")

    def show_toolbox(self):
        play_cyberpunk_beep("click")
        self.toolbox_instance = ToolboxWindow(self)
        
    # Forced Update Configs Downloader
    def force_update_configs(self):
        log_debug("Forced config update initiated.")
        play_cyberpunk_beep("click")
        
        def run_update():
            self.canvas.itemconfig(self.status_text, text="[BAIXANDO...]", fill="#ff9900")
            success = True
            for name, url in cfgs.items():
                path = os.path.join(base_path, name)
                # Force download overwriting existing config files
                if not download_file(url, path, timeout=4):
                    success = False
                time.sleep(0.1)
                
            if success:
                log_debug("Config update complete.")
                self.canvas.itemconfig(self.status_text, text="[CONCLUIDO]", fill="#00ff00")
                play_cyberpunk_beep("success")
            else:
                log_debug("Config update failed.")
                self.canvas.itemconfig(self.status_text, text="[FALHA]", fill="#ff2a2a")
                play_cyberpunk_beep("fail")
                
            # Restore status label after 2 seconds
            active_lbl = "NENHUM"
            if self.active_config:
                for name, btn in self.filter_buttons.items():
                    if name == self.active_config:
                        active_lbl = self.canvas.itemcget(btn["text"], "text")
                        break
            self.root.after(2000, lambda: self.canvas.itemconfig(self.status_text, text=f"[{active_lbl}]", fill="#aaaaaa"))
            
        threading.Thread(target=run_update, daemon=True).start()

    # WinAPI background Hotkey Listener Thread
    def hotkey_listener(self):
        log_debug("Starting global hotkey listener...")
        user32 = ctypes.windll.user32
        
        # Register Alt+1 to Alt+5, Alt+T, Alt+C, F7, F8 hotkeys
        hotkeys = {
            1: (0x0001, 0x31),
            2: (0x0001, 0x32),
            3: (0x0001, 0x33),
            4: (0x0001, 0x34),
            5: (0x0001, 0x35),
            6: (0x0001, 0x54), # Alt+T
            7: (0x0001, 0x43), # Alt+C
            8: (0x0000, 0x76), # F7
            9: (0x0000, 0x77), # F8
            10: (0x0001, 0x53), # Alt+S (Streamer Mode)
            11: (0x0000, 0x78)  # F9 (Town Calibration)
        }
        
        for hk_id, (mod, vk) in hotkeys.items():
            res = user32.RegisterHotKey(None, hk_id, mod, vk)
            log_debug(f"Registering Hotkey ID {hk_id}: {res}")
            
        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312: # WM_HOTKEY
                    hk_id = msg.wParam
                    log_debug(f"Hotkey event received: ID {hk_id}")
                    # Dispatch to main Tkinter thread safely
                    self.root.after(0, self.handle_hotkey, hk_id)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            log_debug(f"Hotkey thread execution error: {e}")
        finally:
            log_debug("Hotkey listener loop stopped. Unregistering keys.")
            for hk_id in hotkeys.keys():
                user32.UnregisterHotKey(None, hk_id)
 
    def handle_hotkey(self, hk_id):
        mapping = {
            1: ("BH_normal.cfg", "NORMAL"),
            2: ("BH_elite.cfg", "ELITE"),
            3: ("BH_rw.cfg", "KAKASHI"),
            4: ("BH_mf.cfg", "MF"),
            5: ("BH_rwall.cfg", "RW ALL")
        }
        if hk_id in mapping:
            config, label = mapping[hk_id]
            log_debug(f"Hotkey triggered swap to: {label}")
            self.swap_filter(config, label)
            play_cyberpunk_beep("success")
        elif hk_id == 6: # Alt+T
            # Trigger run timer split/start in toolbox
            if self.toolbox_instance and tk.Toplevel.winfo_exists(self.toolbox_instance.root):
                self.toolbox_instance.trigger_timer_hotkey()
        elif hk_id == 7: # Alt+C
            # Trigger auto clicker toggle in toolbox
            if self.toolbox_instance and tk.Toplevel.winfo_exists(self.toolbox_instance.root):
                self.toolbox_instance.trigger_autoclicker_hotkey()
        elif hk_id == 8: # F7
            # Trigger HP calibration in toolbox
            if self.toolbox_instance and tk.Toplevel.winfo_exists(self.toolbox_instance.root):
                self.toolbox_instance.trigger_hp_calibration()
        elif hk_id == 9: # F8
            # Trigger MP calibration in toolbox
            if self.toolbox_instance and tk.Toplevel.winfo_exists(self.toolbox_instance.root):
                self.toolbox_instance.trigger_mp_calibration()
        elif hk_id == 10: # Alt+S
            self.toggle_streamer_mode()
        elif hk_id == 11: # F9
            # Trigger Town calibration in toolbox
            if self.toolbox_instance and tk.Toplevel.winfo_exists(self.toolbox_instance.root):
                self.toolbox_instance.trigger_town_calibration()

    def add_alert(self, text, color, duration=2.0):
        alert = {"text": text, "color": color, "expire": time.time() + duration}
        self.active_alerts.append(alert)
        if len(self.active_alerts) > 3:
            self.active_alerts.pop(0)

    def autopot_loop(self):
        log_debug("AutoPot monitoring thread loop started.")
        last_hp_pot_time = 0.0
        last_mp_pot_time = 0.0
        last_rejuv_time = 0.0
        last_esc_time = 0.0
        
        last_state_check = 0.0
        death_detection_start = 0.0
        
        while True:
            try:
                if is_game_active():
                    now = time.time()
                    
                    # --- STATE DETECTION & TELEMETRY ---
                    if now - last_state_check >= 0.2:
                        last_state_check = now
                        
                        # 1. Loading Screen Detection
                        sw = ctypes.windll.user32.GetSystemMetrics(0)
                        sh = ctypes.windll.user32.GetSystemMetrics(1)
                        mid_x, mid_y = sw // 2, sh // 2
                        
                        r1, g1, b1 = get_pixel_color(mid_x, mid_y)
                        r2, g2, b2 = get_pixel_color(mid_x - 50, mid_y - 50)
                        r3, g3, b3 = get_pixel_color(mid_x + 50, mid_y + 50)
                        
                        is_loading = (r1 < 15 and g1 < 15 and b1 < 15 and
                                      r2 < 15 and g2 < 15 and b2 < 15 and
                                      r3 < 15 and g3 < 15 and b3 < 15)
                        
                        if is_loading:
                            if self.game_state != "CARREGANDO":
                                self.game_state = "CARREGANDO"
                                log_debug("Game state: CARREGANDO")
                                if self.toolbox_instance and self.toolbox_instance.timer_running:
                                    self.toolbox_instance.pause_timer()
                        else:
                            # 2. Death Screen Detection
                            is_hp_empty = False
                            if self.hp_pixel_x > 0 and self.hp_pixel_r > 0:
                                hp_r, hp_g, hp_b = get_pixel_color(self.hp_pixel_x, self.hp_pixel_y)
                                if hp_r < 15 and hp_g < 15 and hp_b < 15:
                                    is_hp_empty = True
                                    
                            if is_hp_empty:
                                if death_detection_start == 0.0:
                                    death_detection_start = now
                                elif now - death_detection_start >= 2.0:
                                    if self.game_state != "MORTO":
                                        self.game_state = "MORTO"
                                        self.session_deaths += 1
                                        self.add_alert("💀 JOGADOR MORTO!", "#ff0000", duration=5.0)
                                        log_debug(f"Game state: MORTO. Total deaths: {self.session_deaths}")
                                        if self.toolbox_instance and self.toolbox_instance.timer_running:
                                            self.toolbox_instance.stop_timer()
                            else:
                                death_detection_start = 0.0
                                
                                # 3. Town Detection (via calibrated town pixel)
                                is_town = False
                                if self.town_pixel_enabled and self.town_pixel_x > 0:
                                    t_r, t_g, t_b = get_pixel_color(self.town_pixel_x, self.town_pixel_y)
                                    dist = ((t_r - self.town_pixel_r)**2 + 
                                            (t_g - self.town_pixel_g)**2 + 
                                            (t_b - self.town_pixel_b)**2)**0.5
                                    if dist < 30:
                                        is_town = True
                                        
                                if is_town:
                                    if self.game_state != "CIDADE":
                                        self.game_state = "CIDADE"
                                        log_debug("Game state: CIDADE")
                                        if self.toolbox_instance and self.toolbox_instance.timer_running:
                                            self.toolbox_instance.record_split()
                                else:
                                    if self.game_state != "COMBATE" and self.game_state != "MORTO":
                                        self.game_state = "COMBATE"
                                        log_debug("Game state: COMBATE")
                                        if self.toolbox_instance and not self.toolbox_instance.timer_running:
                                            self.toolbox_instance.start_timer()
                                            
                    # --- AUTO POTION & SMART ASSIST LOGIC ---
                    hp_pct = 100.0
                    mp_pct = 100.0
                    
                    curr_hp_r, curr_hp_g, curr_hp_b = 0, 0, 0
                    curr_mp_r, curr_mp_g, curr_mp_b = 0, 0, 0
                    
                    if self.hp_pixel_x > 0 and self.hp_pixel_r > 0:
                        curr_hp_r, curr_hp_g, curr_hp_b = get_pixel_color(self.hp_pixel_x, self.hp_pixel_y)
                        if curr_hp_g >= 60:
                            hp_pct = 100.0
                        else:
                            hp_pct = (curr_hp_r / self.hp_pixel_r) * 100.0
                            
                    if self.mp_pixel_x > 0 and self.mp_pixel_b > 0:
                        curr_mp_r, curr_mp_g, curr_mp_b = get_pixel_color(self.mp_pixel_x, self.mp_pixel_y)
                        mp_pct = (curr_mp_b / self.mp_pixel_b) * 100.0
                        
                    # HP history for sudden drop check (every 100ms)
                    if now - self.last_hp_sample_time >= 0.1:
                        self.last_hp_sample_time = now
                        self.hp_history.append((now, hp_pct))
                        if len(self.hp_history) > 5:
                            self.hp_history.pop(0)
                            
                        # Sudden drop check (drop of >20% in 300ms)
                        if len(self.hp_history) >= 3:
                            _, oldest_hp = self.hp_history[0]
                            if oldest_hp - hp_pct > 20.0 and now - last_hp_pot_time >= self.autopot_hp_cooldown:
                                log_debug(f"SUDDEN HP DROP DETECTED! HP dropped from {oldest_hp:.1f}% to {hp_pct:.1f}%")
                                self.add_alert("⚠️ RISK OF DEATH - HEAL INJECTED", "#ff0000", duration=2.0)
                                self.session_near_deaths += 1
                                send_pot_key(self.autopot_hp_key)
                                self.session_hp_pots += 1
                                last_hp_pot_time = now
                                
                    # 1. HP Potion Check
                    if self.autopot_hp_enabled and self.hp_pixel_x > 0 and self.hp_pixel_r > 0:
                        if now - last_hp_pot_time >= self.autopot_hp_cooldown:
                            if (curr_hp_r < 120 or curr_hp_r < (self.hp_pixel_r * 0.75)) and curr_hp_g < 60:
                                log_debug(f"HP AutoPot Triggered! Current Red: {curr_hp_r}, Calibrated Red: {self.hp_pixel_r}")
                                self.add_alert("⚡ HP POTION USED", "#ff3333", duration=1.5)
                                send_pot_key(self.autopot_hp_key)
                                self.session_hp_pots += 1
                                last_hp_pot_time = now
                                
                    # 2. MP Potion Check
                    if self.autopot_mp_enabled and self.mp_pixel_x > 0 and self.mp_pixel_b > 0:
                        if now - last_mp_pot_time >= self.autopot_mp_cooldown:
                            if (curr_mp_b < 130 or curr_mp_b < (self.mp_pixel_b * 0.75)) and curr_hp_g < 60:
                                log_debug(f"MP AutoPot Triggered! Current Blue: {curr_mp_b}, Calibrated Blue: {self.mp_pixel_b}")
                                self.add_alert("⚡ MP POTION USED", "#3399ff", duration=1.5)
                                send_pot_key(self.autopot_mp_key)
                                self.session_mp_pots += 1
                                last_mp_pot_time = now
                                
                    # 3. Auto Rejuv Trigger (HP + MP low)
                    if self.auto_rejuv_enabled and self.hp_pixel_x > 0 and self.mp_pixel_x > 0:
                        if now - last_rejuv_time >= 3.0:
                            if hp_pct < self.rejuv_trigger_pct and mp_pct < self.rejuv_trigger_pct:
                                log_debug(f"Emergency Rejuv Triggered! HP: {hp_pct:.1f}%, MP: {mp_pct:.1f}%")
                                self.add_alert("🚨 EMERGENCY REJUVENATION!", "#ee00ff", duration=2.5)
                                send_pot_key(self.rejuv_key)
                                last_rejuv_time = now
                                
                    # 4. Auto ESC Trigger (HP below threshold)
                    if self.auto_esc_enabled and self.hp_pixel_x > 0:
                        if now - last_esc_time >= 10.0:
                            if hp_pct < self.esc_trigger_pct and hp_pct > 0:
                                log_debug(f"Emergency Escape triggered! HP: {hp_pct:.1f}%")
                                self.add_alert("💀 ESCAPE PANIC TRIGGERED!", "#ffaa00", duration=3.0)
                                send_esc_key()
                                last_esc_time = now
                                
            except Exception as e:
                log_debug(f"AutoPot loop error: {e}")
                
            # Manage alert timers
            now = time.time()
            self.active_alerts = [a for a in self.active_alerts if now < a["expire"]]
            
            time.sleep(0.05)

if __name__ == "__main__":
    try:
        KakashiHubApp()
    except Exception as e:
        log_debug(f"Unhandled Exception in main application: {e}")
