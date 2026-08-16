from __future__ import annotations

import os
import platform
import shutil
import subprocess

_TITLE = "turnbreak"
_MESSAGE = "Your agent finished its turn."


def notify_native(timeout: float = 2.0) -> bool:
    """Fire a native OS notification. Returns False, silently, on any failure.

    This is layer 3 of the done signal. Layers 1 and 2 live in the page's
    own JavaScript and must not depend on this succeeding.
    """
    if os.environ.get("TURNBREAK_NO_NOTIFY"):
        return False
    system = platform.system()
    try:
        if system == "Linux":
            return _run_if_available("notify-send", [_TITLE, _MESSAGE], timeout)
        if system == "Darwin":
            script = f'display notification "{_MESSAGE}" with title "{_TITLE}"'
            return _run_if_available("osascript", ["-e", script], timeout)
        if system == "Windows":
            script = (
                "[Windows.UI.Notifications.ToastNotificationManager, "
                "Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null; "
                "[Windows.UI.Notifications.ToastTemplateType, Windows.UI.Notifications, "
                "ContentType=WindowsRuntime] | Out-Null; "
                "$xml = [Windows.UI.Notifications.ToastNotificationManager]::"
                "GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
                "$text = $xml.GetElementsByTagName('text'); "
                f"$text[0].AppendChild($xml.CreateTextNode('{_TITLE}')) | Out-Null; "
                f"$text[1].AppendChild($xml.CreateTextNode('{_MESSAGE}')) | Out-Null; "
                "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
                f"[Windows.UI.Notifications.ToastNotificationManager]::"
                f"CreateToastNotifier('{_TITLE}').Show($toast)"
            )
            return _run_if_available("powershell", ["-NoProfile", "-Command", script], timeout)
    except (OSError, subprocess.SubprocessError):
        return False
    return False


def _run_if_available(command: str, args: list[str], timeout: float) -> bool:
    if not shutil.which(command):
        return False
    subprocess.run([command, *args], check=False, timeout=timeout)
    return True
