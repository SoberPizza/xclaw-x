"""Type text and press keys — delegates to platform-native backend."""

from xclaw.config import HUMANIZE


def type_text(text: str) -> dict:
    """Type text at the current cursor position.

    Args:
        text: The text to type.

    Returns:
        {"status": "ok", "action": "type", "text": text}
    """
    if HUMANIZE:
        from xclaw.action.humanize import humanized_type
        humanized_type(text)
    else:
        from xclaw.action import type_text as _type_text
        _type_text(text)

    return {"status": "ok", "action": "type", "text": text}


def press_key(key: str) -> dict:
    """Press a single key or key combination.

    Args:
        key: Key name (e.g. 'enter', 'tab', 'escape', 'backspace')
             or combo (e.g. 'cmd+c', 'ctrl+shift+s').

    Returns:
        {"status": "ok", "action": "press", "key": key}
    """
    if HUMANIZE:
        import random
        import time as _time
        _time.sleep(random.uniform(0.03, 0.12))

    from xclaw.action import hotkey as _hotkey

    if "+" in key:
        _hotkey(key)
    else:
        _hotkey(key)  # single key works as hotkey with no modifiers

    return {"status": "ok", "action": "press", "key": key}
