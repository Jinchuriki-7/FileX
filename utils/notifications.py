"""
utils/notifications.py
-----------------------
Windows native toast notifications for FileX.
Uses the `win10toast` or falls back to a simple ctypes MessageBeep
so we never crash on import errors.
"""

import threading
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Attempt to import win10toast (optional dependency)
# ---------------------------------------------------------------------------
try:
    from win10toast import ToastNotifier
    _TOAST_AVAILABLE = True
except ImportError:
    _TOAST_AVAILABLE = False


# ---------------------------------------------------------------------------
# Fallback: Windows balloon-tip via ctypes (Shell_NotifyIconW is complex,
# so we just play a system sound as the simplest always-available fallback).
# ---------------------------------------------------------------------------
def _play_system_sound(sound_alias: str = "SystemAsterisk") -> None:
    """Play a Windows system sound (non-blocking)."""
    try:
        import ctypes
        ctypes.windll.winmm.PlaySoundW(sound_alias, None, 0x00010001)  # SND_ALIAS | SND_ASYNC
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public notification helper
# ---------------------------------------------------------------------------

class NotificationManager:
    """
    Wraps Windows toast notifications with a clean, thread-safe interface.

    Usage::

        nm = NotificationManager()
        nm.send("FileX", "Conversion complete!", duration=4)
    """

    def __init__(self) -> None:
        # Icon path for the toast (optional — works without it)
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "images" / "logo.ico"
        self._icon: Optional[str] = str(icon_path) if icon_path.exists() else None
        self._toaster = ToastNotifier() if _TOAST_AVAILABLE else None

    # ------------------------------------------------------------------
    def send(
        self,
        title: str,
        message: str,
        duration: int = 5,
        threaded: bool = True,
    ) -> None:
        """
        Display a Windows toast notification.

        Args:
            title:    Notification title.
            message:  Body text.
            duration: How many seconds the toast stays visible.
            threaded: If True, show the toast in a background thread so the
                      UI is never blocked.
        """
        if threaded:
            t = threading.Thread(
                target=self._show,
                args=(title, message, duration),
                daemon=True,
            )
            t.start()
        else:
            self._show(title, message, duration)

    # ------------------------------------------------------------------
    def _show(self, title: str, message: str, duration: int) -> None:
        """Internal: actually display the notification."""
        try:
            if self._toaster is not None:
                self._toaster.show_toast(
                    title,
                    message,
                    icon_path=self._icon,
                    duration=duration,
                    threaded=False,  # We already handle threading above
                )
            else:
                # Fallback: play a sound + try PowerShell toast
                _play_system_sound()
                self._powershell_toast(title, message)
        except Exception:
            _play_system_sound()

    # ------------------------------------------------------------------
    @staticmethod
    def _powershell_toast(title: str, message: str) -> None:
        """
        Secondary fallback: use PowerShell to show a BurntToast-style
        notification via the Windows.UI.Notifications COM API.
        Only works on Windows 10+ with PowerShell 5+.
        """
        try:
            import subprocess
            # Escape single quotes in title/message
            t = title.replace("'", "\\'")
            m = message.replace("'", "\\'")
            ps_script = (
                "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null; "
                "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null; "
                f"$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent('ToastText02'); "
                f"$xml.GetElementsByTagName('text')[0].InnerText = '{t}'; "
                f"$xml.GetElementsByTagName('text')[1].InnerText = '{m}'; "
                "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
                "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('FileX').Show($toast)"
            )
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Module-level convenience instance
# ---------------------------------------------------------------------------
_default_manager: Optional[NotificationManager] = None


def get_notifier() -> NotificationManager:
    """Return the shared NotificationManager instance (created on first call)."""
    global _default_manager
    if _default_manager is None:
        _default_manager = NotificationManager()
    return _default_manager


def notify(title: str, message: str, duration: int = 5) -> None:
    """
    Module-level shortcut: show a toast notification.

    Args:
        title:    Notification title.
        message:  Body text.
        duration: Seconds the toast is visible.
    """
    get_notifier().send(title, message, duration=duration)
