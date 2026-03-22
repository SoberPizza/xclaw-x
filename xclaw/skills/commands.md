# X-Claw Command Reference

All commands output JSON to stdout. Use `--timing` flag on any command to print timing breakdown to stderr.

## Perception

### `xclaw look`

Observe the screen. Screenshots, diffs against previous state, and auto-decides parsing depth:

| Level | Trigger | What happens |
|-------|---------|--------------|
| L1 | diff < 1% | Return cached elements (instant) |
| L2 | 1% ≤ diff < 15% | Incremental parse on changed regions only |
| L3 | diff ≥ 15% or first run | Full pipeline: YOLO + OCR + SigLIP 2 |

Auto-escalation: consecutive cheap (L1) > 4 times → force L3. Cache > 15s → force L3.

```json
{
  "layout": {
    "columns": [
      {"id": 0, "x_range": [0, 960], "width_pct": 50, "element_count": 30},
      {"id": 1, "x_range": [960, 1920], "width_pct": 50, "element_count": 25}
    ],
    "total_elements": 55,
    "text_count": 30,
    "icon_count": 25
  },
  "elements": [
    {"id": 0, "type": "text", "bbox": [10,20,200,40], "center": [105,30], "content": "File", "col": 0},
    {"id": 1, "type": "icon", "bbox": [210,20,240,40], "center": [225,30], "content": "close", "col": 0}
  ],
  "timing": {"l1_ms": 800, "l2_ms": 1},
  "_meta": {"level": "L3", "changed": true, "diff_ratio": 0.35, "elapsed_ms": 801}
}
```

## Actions

All action commands automatically observe the screen after execution. Response format:

```json
{
  "action": {"status": "ok", "action": "<command>", ...params},
  "perception": {"layout": {...}, "elements": [...]},
  "_meta": {"level": "L2", "changed": true, "diff_ratio": 0.08, "elapsed_ms": 400}
}
```

### `xclaw click <x> <y> [--double]`

Click at screen coordinates. Use `--double` for double-click. Coordinates must come from an element's `center` field.

### `xclaw type <text> [--no-enter]`

Type text at the current cursor position, then automatically press Enter. Use `--no-enter` to skip the Enter press (e.g., when filling a form field before tabbing to the next). CJK characters are handled via clipboard.

### `xclaw press <key>`

Press a key or key combination. The key must include at least one non-modifier key.

**Single keys:** `enter`, `tab`, `escape`, `backspace`, `space`, `delete`, `up`, `down`, `left`, `right`, `home`, `end`, `pageup`, `pagedown`, `f1`-`f12`, `a`-`z`, `0`-`9`

**Modifiers:** `cmd`/`command`, `ctrl`/`control`, `alt`/`option`, `shift`, `fn`

**Combos (use `+`):**
```
xclaw press cmd+a          # Select all
xclaw press cmd+c          # Copy
xclaw press cmd+v          # Paste
xclaw press cmd+t          # New tab
xclaw press cmd+w          # Close tab
xclaw press cmd+l          # Focus address bar
xclaw press cmd+r          # Refresh page
xclaw press cmd+f          # Find
xclaw press ctrl+tab       # Next tab
xclaw press cmd+shift+]    # Next tab (Safari/Chrome)
xclaw press alt+f4         # Close window (Windows)
```

### `xclaw scroll <up|down> <amount> [--x X] [--y Y]`

Scroll the mouse wheel at optional coordinates (default: screen center).

| Amount | Effect |
|--------|--------|
| 1 | ~3 lines (one notch) |
| 3 | ~9 lines (small scroll) |
| **5** | **~15 lines (moderate scroll)** |
| 10+ | ~30+ lines (big scroll) |

### `xclaw wait <seconds>`

Wait, then observe the screen. Use after actions that trigger loading (page navigation, form submission, animations).

## Server

### `xclaw serve`

Long-running stdio JSON-line server. Models loaded once at startup.

```
← {"status": "ready", "version": "0.5.0"}
→ {"command": "look"}
← {"status": "ok", "elements": [...], "_meta": {...}}
→ {"command": "click", "x": 100, "y": 200}
← {"status": "ok", "action": {...}, "perception": {...}}
→ {"command": "type", "text": "hello"}
← {"status": "ok", "action": {"enter": true, ...}, "perception": {...}}
→ {"command": "type", "text": "hello", "enter": false}
← {"status": "ok", "action": {...}, "perception": {...}}
→ {"command": "scroll", "direction": "down", "amount": 5}
← {"status": "ok", "action": {...}, "perception": {...}}
→ {"command": "wait", "seconds": 2}
← {"status": "ok", "action": {...}, "perception": {...}}
```

Close stdin or kill process to exit. Single-threaded, one request at a time.

## `_meta` Field Reference

| Field | Description |
|-------|-------------|
| `level` | Perception level: L1 (cache/diff), L2 (incremental), L3 (full pipeline) |
| `changed` | Whether the screen changed since last observation |
| `diff_ratio` | Pixel change ratio (0.0 = identical, 1.0 = completely different) |
| `elapsed_ms` | Total perception time in milliseconds |
