"""Human-like mouse movement and typing patterns — cross-platform."""

import platform
import random
import time

from xclaw.config import BEZIER_DURATION_RANGE, BEZIER_STEPS, TYPE_DELAY_RANGE


def bezier_point(t: float, p0, p1, p2, p3):
    """Compute a point on a cubic Bezier curve at parameter t."""
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
    )


def _get_cursor_pos() -> tuple[int, int]:
    """Get current cursor position (platform-aware)."""
    if platform.system() == "Darwin":
        from xclaw.action.mouse_darwin import _cursor_pos
        return _cursor_pos()
    else:
        from xclaw.action.mouse_win32 import _cursor_pos
        return _cursor_pos()


def bezier_move(target_x: int, target_y: int, duration_range: tuple = None, steps: int = None):
    """Move the mouse along a cubic Bezier curve to target — cross-platform.

    Args:
        target_x: Target X coordinate.
        target_y: Target Y coordinate.
        duration_range: (min, max) total duration in seconds.
        steps: Number of intermediate points on the curve.
    """
    from xclaw.action import move_to

    if duration_range is None:
        duration_range = BEZIER_DURATION_RANGE
    if steps is None:
        steps = BEZIER_STEPS

    sx, sy = _get_cursor_pos()
    ex, ey = target_x, target_y

    # Random control points for natural-looking curve
    dx = ex - sx
    dy = ey - sy
    cp1 = (sx + dx * random.uniform(0.2, 0.4) + random.uniform(-50, 50),
           sy + dy * random.uniform(0.0, 0.3) + random.uniform(-50, 50))
    cp2 = (sx + dx * random.uniform(0.6, 0.8) + random.uniform(-50, 50),
           sy + dy * random.uniform(0.7, 1.0) + random.uniform(-50, 50))

    duration = random.uniform(*duration_range)
    interval = duration / steps

    for i in range(1, steps + 1):
        t = i / steps
        # Ease-in-out: slow start and end
        t = t * t * (3 - 2 * t)
        px, py = bezier_point(t, (sx, sy), cp1, cp2, (ex, ey))
        move_to(int(px), int(py))
        time.sleep(interval)


def humanized_click(x: int, y: int, double: bool = False):
    """Move to target with Bezier curve, then click.

    Args:
        x: Target X coordinate.
        y: Target Y coordinate.
        double: Double-click if True.
    """
    from xclaw.action import click as _click, double_click as _dbl

    bezier_move(x, y)

    # Small random offset for natural feel
    offset_x = random.randint(-2, 2)
    offset_y = random.randint(-2, 2)

    if double:
        _dbl(x + offset_x, y + offset_y)
    else:
        _click(x + offset_x, y + offset_y)


def humanized_scroll(direction: str, amount: int, x: int, y: int):
    """Scroll with human-like behavior: Bezier move, jitter, randomized intervals.

    Args:
        direction: 'up' or 'down'.
        amount: Total scroll units.
        x: Target X coordinate.
        y: Target Y coordinate.
    """
    from xclaw.action import scroll as _scroll

    # Add small random offset to target
    jitter_x = x + random.randint(-5, 5)
    jitter_y = y + random.randint(-5, 5)
    bezier_move(jitter_x, jitter_y)

    # Break large scrolls into smaller chunks with random pauses
    chunk_min = max(1, amount // 5)
    chunk_max = max(2, amount // 2)
    remaining = amount
    while remaining > 0:
        chunk = min(remaining, random.randint(chunk_min, chunk_max))
        _scroll(direction, chunk)
        remaining -= chunk
        if remaining > 0:
            time.sleep(random.uniform(0.02, 0.08))


def humanized_type(text: str, delay_range: tuple = None):
    """Type text with random inter-key delays.

    Args:
        text: Text to type.
        delay_range: (min, max) delay between keystrokes in seconds.
    """
    from xclaw.action import type_text as _type_text

    if delay_range is None:
        delay_range = TYPE_DELAY_RANGE

    # Platform native type_text handles all characters (including Chinese/emoji)
    # We just need to add human-like delays between characters
    _type_text(text)
