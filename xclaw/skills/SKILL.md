---
name: xclaw
description: "X-Claw: your eyes and hands for the screen. Use this skill whenever you need to interact with the desktop — browse websites, fill forms, click buttons, read screen content, operate any GUI application. Commands: look, click, type, press, scroll, wait."
allowed-tools: Bash(xclaw *), Read
---

You are a visual agent that perceives and manipulates the screen through the `xclaw` CLI. You see the screen as structured JSON (numbered elements with coordinates), and act via native mouse/keyboard events. **You do NOT need a browser API, DevTools, or accessibility tree — you operate like a human: look at the screen, find the target, click/type.**

## When to use this skill

Use `xclaw` for ANY task that involves the screen:

- **Browse the web**: open URLs, click links, fill forms, search, navigate tabs
- **Read screen content**: extract text, check UI state, verify results
- **Operate any GUI app**: Finder, Terminal, System Settings, VS Code, Slack, etc.
- **Automate workflows**: multi-step sequences across apps (copy from browser → paste into editor)

If the task involves "open", "go to", "click", "search on", "check the page", "fill in", "download from" — **use this skill**.

## Resources

- Complete command reference: [commands.md](commands.md)

## Operating Guidelines

### Core Rules

1. **Look first**: Always start with `xclaw look` to observe the current screen state.
2. **Never guess coordinates**: Only use `center` coordinates from the latest perception result.
3. **Match by content, act by center**: Find elements by their `content` field, click using their `center` `[x, y]`.
4. **Every action returns the new screen state** — you don't need to `look` again after click/type/press/scroll. Only `look` manually at the start or after a `wait`.
5. **Wait for transitions**: Use `xclaw wait <seconds>` when expecting page loads, animations, or network requests.

### Browser Workflow Example

```bash
# 1. Observe current screen
xclaw look

# 2. Click the browser address bar (find it by content/position)
xclaw click 756 52

# 3. Select all existing text and type new URL
xclaw press cmd+a
xclaw type "https://github.com"
xclaw press enter

# 4. Wait for page to load
xclaw wait 2

# 5. Screen is auto-observed after wait — find and click a link
xclaw click 400 350

# 6. Scroll down to read more
xclaw scroll down 500
```

### Element Targeting Strategy

Each `elements[]` entry looks like:
```json
{"id": 42, "type": "text", "bbox": [100, 200, 300, 220], "center": [200, 210], "content": "Sign in", "col": 1}
```

- **`type`**: `"text"` (OCR-detected) or `"icon"` (YOLO-detected, may have label)
- **`content`**: The visible text or icon label — use this to find your target
- **`center`**: `[x, y]` — always use this for click coordinates
- **`col`**: Column index — helps locate elements in multi-column layouts

**Finding targets:**
1. Scan `elements` for matching `content` (partial match is fine)
2. If multiple matches, use `col` and spatial position (`bbox`) to disambiguate
3. For icons without text labels, look at nearby text elements for context

### Key Combos (macOS)

| Action | Command |
|--------|---------|
| Select all | `xclaw press cmd+a` |
| Copy | `xclaw press cmd+c` |
| Paste | `xclaw press cmd+v` |
| Undo | `xclaw press cmd+z` |
| New tab | `xclaw press cmd+t` |
| Close tab | `xclaw press cmd+w` |
| Switch tab | `xclaw press cmd+shift+]` or `cmd+shift+[` |
| Find | `xclaw press cmd+f` |
| Refresh | `xclaw press cmd+r` |
| Address bar | `xclaw press cmd+l` |

### Tips

- **Address bar shortcut**: `xclaw press cmd+l` selects the address bar in any browser — faster than clicking.
- **Scroll amounts**: Use 500+ for visible scrolling, 1000+ for large jumps. Values under 100 are barely noticeable.
- **Page load**: After pressing Enter on a URL or submitting a form, always `xclaw wait 2` (or more for slow sites).
- **Disambiguate**: If the screen has duplicate buttons (e.g. multiple "Submit"), use their `col` and `bbox` position to pick the right one.
- **Chinese input**: `xclaw type` handles CJK characters automatically via clipboard.
