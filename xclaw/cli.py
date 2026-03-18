import json
import time

import click


def _output(data: dict):
    """Print JSON to stdout for LLM consumption."""
    click.echo(json.dumps(data, ensure_ascii=True))


def _extract_ts(image_path: str) -> int | None:
    """Extract millisecond timestamp from 'screen_1234567890123.png'."""
    import re
    m = re.search(r"screen_(\d+)\.", image_path)
    return int(m.group(1)) if m else None


def _save_to_logs(result_dict: dict, *, prefix: str = "screen", timestamp: int | None = None) -> str | None:
    """Persist result to LOGS_DIR. Returns file path or None on failure."""
    from xclaw.config import LOGS_DIR
    try:
        LOGS_DIR.mkdir(exist_ok=True)
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        log_file = LOGS_DIR / f"{prefix}_{timestamp}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        latest_file = LOGS_DIR / f"{prefix}.json"
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        return str(log_file)
    except Exception as exc:
        click.echo(f"Warning: failed to save log: {exc}", err=True)
        return None


def _action_with_look(action_result: dict) -> dict:
    """Run the smart perception scheduler after an action and return combined result."""
    from xclaw.core.context.scheduler import schedule

    sr = schedule(action_result)
    perception = sr.perception
    meta = perception.pop("_perception", {})
    return {
        "action": action_result,
        "perception": perception,
        "_meta": {
            "level": sr.level,
            "confidence": round(sr.confidence, 2),
            "changed": meta.get("changed"),
            "diff_ratio": meta.get("diff_ratio"),
            "elapsed_ms": sr.elapsed_ms,
        },
    }


@click.group()
def main():
    """X-Claw Visual Agent CLI"""
    pass


# ── Perception ────────────────────────────────────────────────────


@main.command()
def init():
    """Initialize X-Claw: verify models and dependencies."""
    import sys
    from xclaw.core.perception.omniparser import get_parser

    try:
        click.echo("Initializing X-Claw...", err=True)
        click.echo("Loading OmniParser models (this may take a while on first run)...", err=True)

        parser = get_parser(suppress_logs=False)

        click.echo("✓ OmniParser initialized successfully", err=True)
        click.echo("✓ All models loaded", err=True)

        _output({
            "status": "ok",
            "message": "X-Claw initialization complete",
            "components": {
                "omniparser": "ready",
                "device": "cuda" if __import__('torch').cuda.is_available() else "cpu",
            }
        })
    except Exception as e:
        click.echo(f"✗ Initialization failed: {e}", err=True)
        _output({
            "status": "error",
            "error": str(e),
        })
        sys.exit(1)


@main.command()
def look():
    """Observe the screen."""
    from xclaw.core.context.scheduler import schedule

    sr = schedule()
    perception = sr.perception
    meta = perception.pop("_perception", {})
    result = {
        **perception,
        "_meta": {
            "level": sr.level,
            "confidence": round(sr.confidence, 2),
            "changed": meta.get("changed"),
            "diff_ratio": meta.get("diff_ratio"),
            "elapsed_ms": sr.elapsed_ms,
        },
    }
    _save_to_logs(result)
    _output(result)


# ── Actions ───────────────────────────────────────────────────────


@main.command("click")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.option("--double", is_flag=True, help="Double-click")
def click_cmd(x, y, double):
    """Click at screen coordinates."""
    from xclaw.action.mouse import click as do_click

    result = do_click(x, y, double=double)
    _output(_action_with_look(result))


@main.command("type")
@click.argument("text")
def type_cmd(text):
    """Type text at the cursor."""
    from xclaw.action.keyboard import type_text

    result = type_text(text)
    _output(_action_with_look(result))


@main.command()
@click.argument("key")
def press(key):
    """Press a key (enter, tab, escape, ...)."""
    from xclaw.action.keyboard import press_key

    result = press_key(key)
    _output(_action_with_look(result))


@main.command()
@click.argument("direction", type=click.Choice(["up", "down"]))
@click.argument("amount", type=int)
@click.option("--x", type=int, default=None, help="X coordinate (default: screen center)")
@click.option("--y", type=int, default=None, help="Y coordinate (default: screen center)")
def scroll(direction, amount, x, y):
    """Scroll up or down."""
    from xclaw.action.mouse import scroll as do_scroll

    result = do_scroll(direction, amount, x, y)
    _output(_action_with_look(result))


@main.command()
@click.argument("seconds", type=float)
def wait(seconds):
    """Wait for a number of seconds."""
    time.sleep(seconds)
    result = {"status": "ok", "action": "wait", "seconds": seconds}
    _output(_action_with_look(result))


if __name__ == "__main__":
    main()
