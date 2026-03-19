"""Click and scroll — delegates to platform-native backend."""

import time

from xclaw.config import HUMANIZE


def click(x: int, y: int, double: bool = False) -> dict:
    """Click at the given screen coordinates.

    Args:
        x: X coordinate.
        y: Y coordinate.
        double: If True, double-click.

    Returns:
        {"status": "ok", "action": "click", "x": x, "y": y, "double": double}
    """
    if HUMANIZE:
        from xclaw.action.humanize import humanized_click
        humanized_click(x, y, double=double)
    else:
        from xclaw.action import click as _click, double_click as _dbl
        if double:
            _dbl(x, y)
        else:
            _click(x, y)
    return {"status": "ok", "action": "click", "x": x, "y": y, "double": double}


def scroll(direction: str, amount: int, x: int | None = None, y: int | None = None) -> dict:
    """Scroll the mouse wheel.

    Args:
        direction: 'up' or 'down'.
        amount: Number of scroll units.
        x: Optional X coordinate to move mouse before scrolling.
        y: Optional Y coordinate to move mouse before scrolling.

    Returns:
        {"status": "ok", "action": "scroll", "direction": direction, "amount": amount, "x": x, "y": y}
    """
    from xclaw.action import move_to, scroll as _scroll

    # If coordinates not specified, default to screen center
    if x is None or y is None:
        import platform as _plat
        if _plat.system() == "Darwin":
            from xclaw.action.mouse_darwin import _screen_size
        else:
            from xclaw.action.mouse_win32 import _screen_size
        sw, sh = _screen_size()
        x = sw // 2
        y = sh // 2

    if HUMANIZE:
        from xclaw.action.humanize import humanized_scroll
        humanized_scroll(direction, amount, x, y)
    else:
        move_to(x, y)
        time.sleep(0.1)
        _scroll(direction, amount)

    return {"status": "ok", "action": "scroll", "direction": direction, "amount": amount, "x": x, "y": y}
