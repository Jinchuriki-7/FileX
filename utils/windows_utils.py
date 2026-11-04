"""
utils/windows_utils.py
-----------------------
Windows-specific helpers: DWM blur, taskbar hide, startup registry, etc.
All ctypes calls are wrapped in try/except so the app still runs on
non-Windows platforms or if a particular API is unavailable.
"""

import os
import sys
import ctypes
import winreg
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# DPI awareness
# ---------------------------------------------------------------------------

def set_dpi_awareness() -> None:
    """Enable Per-Monitor DPI awareness for crisp rendering on HiDPI screens."""
    try:
        # Windows 8.1+ — per-monitor DPI
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # Windows Vista+ fallback
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Window attribute helpers (requires win32 or ctypes)
# ---------------------------------------------------------------------------

def set_window_always_on_top(hwnd: int, enable: bool = True) -> None:
    """
    Set or clear the TOPMOST flag for a native window handle.

    Args:
        hwnd:   Native window handle (obtain via QWidget.winId()).
        enable: True to pin on top, False to unpin.
    """
    HWND_TOPMOST    = -1
    HWND_NOTOPMOST  =  0
    SWP_NOMOVE      = 0x0002
    SWP_NOSIZE      = 0x0001
    SWP_NOACTIVATE  = 0x0010

    insert_after = HWND_TOPMOST if enable else HWND_NOTOPMOST
    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    try:
        ctypes.windll.user32.SetWindowPos(hwnd, insert_after, 0, 0, 0, 0, flags)
    except Exception:
        pass


def enable_acrylic_blur(hwnd: int) -> None:
    """
    Attempt to enable the Windows Acrylic / DWM blur-behind effect.
    Silently ignored on older Windows versions.
    """
    try:
        # Windows 10 1903+ accent policy approach
        ACCENT_ENABLE_ACRYLICBLURBEHIND = 4

        class AccentPolicy(ctypes.Structure):
            _fields_ = [
                ("AccentState",   ctypes.c_int),
                ("AccentFlags",   ctypes.c_int),
                ("GradientColor", ctypes.c_int),
                ("AnimationId",   ctypes.c_int),
            ]

        class WindowCompositionAttribData(ctypes.Structure):
            _fields_ = [
                ("Attribute",  ctypes.c_int),
                ("Data",       ctypes.POINTER(AccentPolicy)),
                ("SizeOfData", ctypes.c_size_t),
            ]

        accent = AccentPolicy()
        accent.AccentState   = ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.AccentFlags   = 0x20   # enable blur on transparent
        accent.GradientColor = 0x99202020  # ARGB semi-transparent dark

        data = WindowCompositionAttribData()
        data.Attribute  = 19   # WCA_ACCENT_POLICY
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data       = ctypes.pointer(accent)

        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Windows startup registry
# ---------------------------------------------------------------------------

APP_NAME = "FileX"
REG_RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def add_to_startup() -> bool:
    """
    Add FileX to Windows startup via the HKCU registry Run key.

    Returns:
        True on success, False on failure.
    """
    try:
        executable = sys.executable
        script = str(Path(__file__).resolve().parent.parent / "main.py")
        value = f'"{executable}" "{script}"'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, value)
        return True
    except Exception:
        return False


def remove_from_startup() -> bool:
    """
    Remove FileX from Windows startup.

    Returns:
        True on success, False on failure.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
        return True
    except FileNotFoundError:
        return True   # Already absent — that's fine
    except Exception:
        return False


def is_in_startup() -> bool:
    """Return True if FileX is registered in the Windows startup Run key."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Taskbar / system tray helpers
# ---------------------------------------------------------------------------

def hide_from_taskbar(hwnd: int) -> None:
    """
    Remove the window from the Windows taskbar while keeping it visible.
    Uses the WS_EX_TOOLWINDOW extended style trick.
    """
    WS_EX_TOOLWINDOW = 0x00000080
    GWL_EXSTYLE = -20
    try:
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_TOOLWINDOW)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Clipboard helper
# ---------------------------------------------------------------------------

def copy_text_to_clipboard(text: str) -> bool:
    """
    Copy *text* to the Windows clipboard using ctypes.

    Returns:
        True on success.
    """
    try:
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        # Encode as UTF-16-LE (CF_UNICODETEXT)
        data = (text + "\0").encode("utf-16-le")
        h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, len(data))  # GMEM_MOVEABLE | GMEM_ZEROINIT
        ptr = ctypes.windll.kernel32.GlobalLock(h_mem)
        ctypes.memmove(ptr, data, len(data))
        ctypes.windll.kernel32.GlobalUnlock(h_mem)
        ctypes.windll.user32.SetClipboardData(13, h_mem)   # CF_UNICODETEXT = 13
        ctypes.windll.user32.CloseClipboard()
        return True
    except Exception:
        return False
