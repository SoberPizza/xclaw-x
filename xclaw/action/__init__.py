"""Action layer platform router.

Windows: ctypes SendInput
macOS:   Quartz CGEvent
"""

import platform

_system = platform.system()

if _system == "Windows":
    from xclaw.action.mouse_win32 import click, double_click, scroll, move_to
    from xclaw.action.keyboard_win32 import type_text, hotkey
elif _system == "Darwin":
    from xclaw.action.mouse_darwin import click, double_click, scroll, move_to
    from xclaw.action.keyboard_darwin import type_text, hotkey
else:
    raise OSError(f"Unsupported platform: {_system}")

__all__ = ["click", "double_click", "scroll", "move_to", "type_text", "hotkey"]
