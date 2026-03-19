"""macOS permission detection and guidance."""

import platform
import subprocess

from rich.console import Console

console = Console()


def check_permissions() -> bool:
    """Check platform permissions at startup. Returns True if all OK.

    Windows: always returns True.
    macOS: checks Accessibility and Screen Recording permissions.
    """
    if platform.system() != "Darwin":
        return True

    ok = True

    # 1. Accessibility (required for mouse/keyboard control)
    if not _check_accessibility():
        console.print("[bold red]❌ 需要辅助功能权限 (Accessibility)[/]")
        console.print("   系统设置 → 隐私与安全性 → 辅助功能")
        console.print("   将你使用的终端 (Terminal / iTerm / Warp) 加入列表")
        console.print()
        subprocess.run([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        ])
        ok = False

    # 2. Screen Recording (required for screenshots)
    if not _check_screen_recording():
        console.print("[bold red]❌ 需要屏幕录制权限 (Screen Recording)[/]")
        console.print("   系统设置 → 隐私与安全性 → 屏幕录制")
        console.print("   将你使用的终端加入列表")
        console.print()
        subprocess.run([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        ])
        ok = False

    if ok:
        console.print("[green]✅ macOS permissions OK[/]")

    return ok


def _check_accessibility() -> bool:
    """Check Accessibility permission via Quartz CGEvent probe."""
    try:
        import Quartz

        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, (0, 0), 0
        )
        return event is not None
    except Exception:
        return False


def _check_screen_recording() -> bool:
    """Test Screen Recording permission by checking if screenshot is not all-black."""
    try:
        import mss

        with mss.mss() as sct:
            img = sct.grab(sct.monitors[1])
            # Without permission, screenshot returns all-black
            raw = img.raw[:1000]
            return sum(raw) > 0
    except Exception:
        return False
