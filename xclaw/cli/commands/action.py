"""Action commands — click, type, press, scroll, wait."""

import json
import time
import logging

import click

from xclaw.cli.core import output

logger = logging.getLogger(__name__)


def _action_with_look(action_result: dict) -> str:
    """Execute action then run full perception, return combined JSON."""
    from xclaw.core.perception.engine import PerceptionEngine

    engine = PerceptionEngine.get_instance()
    perception = engine.full_look()
    combined = {
        "action": action_result,
        "perception": perception,
    }
    return json.dumps(combined, ensure_ascii=False)


@click.command("click")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.option("--double", is_flag=True, help="Double-click")
def click_cmd(x, y, double):
    """Click at screen coordinates."""
    from xclaw.action.mouse import click as do_click

    result = do_click(x, y, double=double)
    output(_action_with_look(result))


@click.command("type")
@click.argument("text")
def type_cmd(text):
    """Type text at the cursor."""
    from xclaw.action.keyboard import type_text

    result = type_text(text)
    output(_action_with_look(result))


@click.command()
@click.argument("key")
def press(key):
    """Press a key (enter, tab, escape, ...)."""
    from xclaw.action.keyboard import press_key

    result = press_key(key)
    output(_action_with_look(result))


@click.command()
@click.argument("direction", type=click.Choice(["up", "down"]))
@click.argument("amount", type=int)
@click.option("--x", type=int, default=None, help="X coordinate (default: screen center)")
@click.option("--y", type=int, default=None, help="Y coordinate (default: screen center)")
def scroll(direction, amount, x, y):
    """Scroll up or down."""
    from xclaw.action.mouse import scroll as do_scroll

    result = do_scroll(direction, amount, x, y)
    output(_action_with_look(result))


@click.command()
@click.argument("seconds", type=float)
def wait(seconds):
    """Wait for a number of seconds."""
    time.sleep(seconds)
    result = {"status": "ok", "action": "wait", "seconds": seconds}
    output(_action_with_look(result))
