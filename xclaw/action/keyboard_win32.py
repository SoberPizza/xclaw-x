"""Windows keyboard control via ctypes SendInput.

Four input paths:
  A) VK physical key simulation for ASCII characters (with IME detection)
  B) Clipboard paste for non-ASCII characters (fallback)
  C) KEYEVENTF_UNICODE as internal fallback (supports surrogate pairs)
  D) IMM32 composition injection for CJK text (generates real IME events)
"""

import ctypes
import ctypes.wintypes
import time
import random
import logging

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
imm32 = ctypes.windll.imm32

# ── ctypes function signatures (64-bit safe) ──
# Without explicit restype, ctypes defaults to c_int (32-bit) which
# truncates 64-bit pointers/handles on x64 Windows — causing clipboard
# corruption and IME detection failure.
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalFree.argtypes = [ctypes.c_void_p]

user32.GetClipboardData.restype = ctypes.c_void_p
user32.GetClipboardData.argtypes = [ctypes.c_uint]
user32.SetClipboardData.restype = ctypes.c_void_p
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.OpenClipboard.argtypes = [ctypes.c_void_p]
user32.GetForegroundWindow.restype = ctypes.c_void_p

imm32.ImmGetContext.restype = ctypes.c_void_p
imm32.ImmGetContext.argtypes = [ctypes.c_void_p]
imm32.ImmGetConversionStatus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.POINTER(ctypes.wintypes.DWORD)]
imm32.ImmReleaseContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

# ImmGetDefaultIMEWnd — get the default IME window for WM_IME_CONTROL
imm32.ImmGetDefaultIMEWnd.restype = ctypes.c_void_p
imm32.ImmGetDefaultIMEWnd.argtypes = [ctypes.c_void_p]

# ImmSetConversionStatus — set IME conversion mode (official API)
imm32.ImmSetConversionStatus.restype = ctypes.c_int
imm32.ImmSetConversionStatus.argtypes = [
    ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
]

# SendMessageW — for WM_IME_CONTROL messages
user32.SendMessageW.restype = ctypes.wintypes.LPARAM
user32.SendMessageW.argtypes = [
    ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p,
]

# ImmSetCompositionStringW — inject composition text into the IME pipeline
SCS_SETSTR = 0x9
imm32.ImmSetCompositionStringW.restype = ctypes.c_int
imm32.ImmSetCompositionStringW.argtypes = [
    ctypes.c_void_p,  # hIMC
    ctypes.c_ulong,   # dwIndex (SCS_SETSTR)
    ctypes.c_wchar_p, # lpComp (composition string)
    ctypes.c_ulong,   # dwCompLen (byte length)
    ctypes.c_wchar_p, # lpRead (reading string, NULL)
    ctypes.c_ulong,   # dwReadLen
]

# ImmNotifyIME — tell IME to commit the composition
NI_COMPOSITIONSTR = 0x0015
CPS_COMPLETE = 0x0001
imm32.ImmNotifyIME.restype = ctypes.c_int
imm32.ImmNotifyIME.argtypes = [
    ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong,
]

user32.VkKeyScanW.restype = ctypes.c_short
user32.VkKeyScanW.argtypes = [ctypes.c_wchar]

# MapVirtualKeyW — translate VK to hardware scan code
MAPVK_VK_TO_VSC = 0
user32.MapVirtualKeyW.restype = ctypes.c_uint
user32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]

# SendInput constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

# Clipboard constants
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

# IME conversion mode flags
IME_CMODE_ALPHANUMERIC = 0x0000
IME_CMODE_NATIVE = 0x0001

# WM_IME_CONTROL message and sub-commands
WM_IME_CONTROL = 0x0283
IMC_GETCONVERSIONMODE = 0x0001
IMC_SETCONVERSIONMODE = 0x0002

# IME toggle timing
_IME_SETTLE_DELAY = (0.10, 0.20)  # seconds for TSF pipeline propagation
_MAX_IME_TOGGLE_ATTEMPTS = 3

# Windows Virtual Key codes
WIN_VK = {
    "return": 0x0D, "enter": 0x0D, "tab": 0x09, "space": 0x20,
    "backspace": 0x08, "delete": 0x2E, "escape": 0x1B, "esc": 0x1B,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "ctrl": 0x11, "control": 0x11, "lctrl": 0xA2, "rctrl": 0xA3,
    "shift": 0x10, "lshift": 0xA0, "rshift": 0xA1,
    "alt": 0x12, "lalt": 0xA4, "ralt": 0xA5,
    "win": 0x5B, "lwin": 0x5B, "rwin": 0x5C,
    "capslock": 0x14, "numlock": 0x90, "scrolllock": 0x91,
    "insert": 0x2D, "printscreen": 0x2C,
    "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45,
    "f": 0x46, "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A,
    "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F,
    "p": 0x50, "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54,
    "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59, "z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
}

# Modifier VK codes
WIN_MOD_VK = {
    "ctrl": 0x11, "control": 0x11,
    "shift": 0x10,
    "alt": 0x12,
    "win": 0x5B,
}

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt key


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    # Windows INPUT union 的大小取最大成员（MOUSEINPUT = 32 bytes），
    # 如果只放 KEYBDINPUT（24 bytes），sizeof(INPUT) 会少 8 bytes，
    # 导致 SendInput 因 cbSize 不匹配而静默失败。
    # 用 _pad 填充到 MOUSEINPUT 的大小以保证结构体正确。
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("_pad", ctypes.c_ubyte * 32),
        ]

    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("_input", _INPUT_UNION),
    ]


# ── Low-level SendInput helpers ──


def _send_key(vk: int = 0, scan: int = 0, flags: int = 0):
    # Auto-fill hardware scan code for VK events so that Chrome's
    # KeyboardEvent.code is non-empty (empty code = bot fingerprint).
    if vk and not scan and not (flags & KEYEVENTF_UNICODE):
        scan = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.ki.wVk = vk
    inp.ki.wScan = scan
    inp.ki.dwFlags = flags
    inp.ki.time = 0
    inp.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _press_release_vk(vk: int):
    _send_key(vk=vk)
    time.sleep(random.uniform(0.02, 0.06))
    _send_key(vk=vk, flags=KEYEVENTF_KEYUP)


# ── Path C: KEYEVENTF_UNICODE (internal fallback, supports surrogate pairs) ──


def _type_unicode_char(char: str):
    """Send a Unicode character via KEYEVENTF_UNICODE.

    Handles BMP characters directly and supplementary plane characters
    (e.g. emoji) as UTF-16 surrogate pairs.
    """
    code = ord(char)
    if code <= 0xFFFF:
        # BMP character — single event pair
        _send_key(scan=code, flags=KEYEVENTF_UNICODE)
        time.sleep(random.uniform(0.02, 0.06))
        _send_key(scan=code, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
    else:
        # Supplementary plane — UTF-16 surrogate pair
        high = 0xD800 + ((code - 0x10000) >> 10)
        low = 0xDC00 + ((code - 0x10000) & 0x3FF)
        _send_key(scan=high, flags=KEYEVENTF_UNICODE)
        _send_key(scan=low, flags=KEYEVENTF_UNICODE)
        time.sleep(random.uniform(0.02, 0.06))
        _send_key(scan=low, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)
        _send_key(scan=high, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)


# ── IME detection and control ──


def _get_foreground_ime_context():
    """Get IME context for the foreground window."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None, None
    himc = imm32.ImmGetContext(hwnd)
    return hwnd, himc


def _is_ime_chinese_mode() -> bool:
    """Check if the current IME is in Chinese (non-alphanumeric) input mode.

    Uses two detection methods for reliability on both IMM32 and TSF IMEs:
    1. WM_IME_CONTROL via SendMessageW (works on TSF/Microsoft Pinyin)
    2. ImmGetConversionStatus fallback (works on IMM32/legacy IMEs)
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    # Method 1: WM_IME_CONTROL via IME default window (TSF-reliable)
    ime_wnd = imm32.ImmGetDefaultIMEWnd(hwnd)
    if ime_wnd:
        mode = user32.SendMessageW(
            ime_wnd, WM_IME_CONTROL,
            ctypes.c_void_p(IMC_GETCONVERSIONMODE), ctypes.c_void_p(0),
        )
        return (mode & IME_CMODE_NATIVE) != 0

    # Method 2: ImmGetConversionStatus fallback (legacy IMEs)
    himc = imm32.ImmGetContext(hwnd)
    if not himc:
        return False
    conversion = ctypes.wintypes.DWORD()
    sentence = ctypes.wintypes.DWORD()
    result = imm32.ImmGetConversionStatus(
        himc, ctypes.byref(conversion), ctypes.byref(sentence)
    )
    imm32.ImmReleaseContext(hwnd, himc)
    if not result:
        return False
    return (conversion.value & IME_CMODE_NATIVE) != 0


def _ensure_ime_english() -> bool:
    """Ensure IME is in English/alphanumeric mode. Returns True if successful.

    Tries three methods with verification, falling back on failure:
    1. WM_IME_CONTROL + IMC_SETCONVERSIONMODE (TSF-reliable)
    2. ImmSetConversionStatus (official API, may not work on TSF)
    3. VK_SHIFT toggle (legacy, unreliable)

    Idempotent: safe to call before every ASCII segment.
    """
    if not _is_ime_chinese_mode():
        return True

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    # Method 1: WM_IME_CONTROL + IMC_SETCONVERSIONMODE
    ime_wnd = imm32.ImmGetDefaultIMEWnd(hwnd)
    if ime_wnd:
        current_mode = user32.SendMessageW(
            ime_wnd, WM_IME_CONTROL,
            ctypes.c_void_p(IMC_GETCONVERSIONMODE), ctypes.c_void_p(0),
        )
        new_mode = current_mode & ~IME_CMODE_NATIVE
        user32.SendMessageW(
            ime_wnd, WM_IME_CONTROL,
            ctypes.c_void_p(IMC_SETCONVERSIONMODE), ctypes.c_void_p(new_mode),
        )
        time.sleep(random.uniform(*_IME_SETTLE_DELAY))
        if not _is_ime_chinese_mode():
            return True

    # Method 2: ImmSetConversionStatus
    himc = imm32.ImmGetContext(hwnd)
    if himc:
        conversion = ctypes.wintypes.DWORD()
        sentence = ctypes.wintypes.DWORD()
        if imm32.ImmGetConversionStatus(
            himc, ctypes.byref(conversion), ctypes.byref(sentence),
        ):
            new_conv = conversion.value & ~IME_CMODE_NATIVE
            imm32.ImmSetConversionStatus(himc, new_conv, sentence.value)
            time.sleep(random.uniform(*_IME_SETTLE_DELAY))
        imm32.ImmReleaseContext(hwnd, himc)
        if not _is_ime_chinese_mode():
            return True

    # Method 3: VK_SHIFT toggle (legacy, unreliable)
    for _ in range(_MAX_IME_TOGGLE_ATTEMPTS):
        _send_key(vk=VK_SHIFT)
        time.sleep(random.uniform(0.03, 0.08))
        _send_key(vk=VK_SHIFT, flags=KEYEVENTF_KEYUP)
        time.sleep(random.uniform(*_IME_SETTLE_DELAY))
        if not _is_ime_chinese_mode():
            return True

    logger.warning("Failed to switch IME to English mode after all methods")
    return False


def _restore_ime_chinese() -> bool:
    """Restore IME to Chinese/native mode. Returns True if successful.

    Mirror of _ensure_ime_english() but sets the native flag.
    """
    if _is_ime_chinese_mode():
        return True

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    # Method 1: WM_IME_CONTROL
    ime_wnd = imm32.ImmGetDefaultIMEWnd(hwnd)
    if ime_wnd:
        current_mode = user32.SendMessageW(
            ime_wnd, WM_IME_CONTROL,
            ctypes.c_void_p(IMC_GETCONVERSIONMODE), ctypes.c_void_p(0),
        )
        new_mode = current_mode | IME_CMODE_NATIVE
        user32.SendMessageW(
            ime_wnd, WM_IME_CONTROL,
            ctypes.c_void_p(IMC_SETCONVERSIONMODE), ctypes.c_void_p(new_mode),
        )
        time.sleep(random.uniform(*_IME_SETTLE_DELAY))
        if _is_ime_chinese_mode():
            return True

    # Method 2: ImmSetConversionStatus
    himc = imm32.ImmGetContext(hwnd)
    if himc:
        conversion = ctypes.wintypes.DWORD()
        sentence = ctypes.wintypes.DWORD()
        if imm32.ImmGetConversionStatus(
            himc, ctypes.byref(conversion), ctypes.byref(sentence),
        ):
            new_conv = conversion.value | IME_CMODE_NATIVE
            imm32.ImmSetConversionStatus(himc, new_conv, sentence.value)
            time.sleep(random.uniform(*_IME_SETTLE_DELAY))
        imm32.ImmReleaseContext(hwnd, himc)
        if _is_ime_chinese_mode():
            return True

    # Method 3: VK_SHIFT toggle
    _send_key(vk=VK_SHIFT)
    time.sleep(random.uniform(0.03, 0.08))
    _send_key(vk=VK_SHIFT, flags=KEYEVENTF_KEYUP)
    time.sleep(random.uniform(*_IME_SETTLE_DELAY))
    return _is_ime_chinese_mode()


# ── Path D: IMM32 composition injection (CJK text) ──


def ime_compose(text: str) -> bool:
    """Inject text through the IMM32 composition pipeline.

    This causes Windows to send WM_IME_COMPOSITION / WM_IME_ENDCOMPOSITION
    to the target window.  Chrome (via the CUAS compatibility layer) translates
    these into standard JS composition events — identical to real IME input.

    Returns True on success, False if the IME context is unavailable
    (caller should fall back to clipboard_paste).
    """
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    himc = imm32.ImmGetContext(hwnd)
    if not himc:
        return False
    try:
        byte_len = len(text.encode("utf-16-le"))
        ok = imm32.ImmSetCompositionStringW(
            himc, SCS_SETSTR, text, byte_len, None, 0,
        )
        if not ok:
            return False
        imm32.ImmNotifyIME(himc, NI_COMPOSITIONSTR, CPS_COMPLETE, 0)
        time.sleep(random.uniform(0.02, 0.06))
        return True
    finally:
        imm32.ImmReleaseContext(hwnd, himc)


# ── Path A: VK physical key simulation (ASCII) ──


def type_char_vk(char: str):
    """Type a single ASCII character using VK physical key simulation.

    Uses VkKeyScanW to map the character to VK + shift state for the
    current keyboard layout. Handles Shift, Ctrl, and Alt modifiers
    (needed for AltGr characters on non-US layouts).
    Falls back to KEYEVENTF_UNICODE if the character has no VK mapping.
    """
    result = user32.VkKeyScanW(char)
    if result == -1:
        # No VK mapping on current layout — fallback
        _type_unicode_char(char)
        return

    vk = result & 0xFF
    shift_state = (result >> 8) & 0xFF
    need_shift = bool(shift_state & 0x01)
    need_ctrl = bool(shift_state & 0x02)
    need_alt = bool(shift_state & 0x04)

    # Press modifiers
    if need_ctrl:
        _send_key(vk=VK_CONTROL)
        time.sleep(random.uniform(0.01, 0.03))
    if need_alt:
        _send_key(vk=VK_MENU)
        time.sleep(random.uniform(0.01, 0.03))
    if need_shift:
        _send_key(vk=VK_SHIFT)
        time.sleep(random.uniform(0.01, 0.03))

    _send_key(vk=vk)
    time.sleep(random.uniform(0.02, 0.06))
    _send_key(vk=vk, flags=KEYEVENTF_KEYUP)

    # Release modifiers (reverse order)
    if need_shift:
        time.sleep(random.uniform(0.01, 0.03))
        _send_key(vk=VK_SHIFT, flags=KEYEVENTF_KEYUP)
    if need_alt:
        time.sleep(random.uniform(0.01, 0.03))
        _send_key(vk=VK_MENU, flags=KEYEVENTF_KEYUP)
    if need_ctrl:
        time.sleep(random.uniform(0.01, 0.03))
        _send_key(vk=VK_CONTROL, flags=KEYEVENTF_KEYUP)


# ── Path B: Clipboard paste (non-ASCII) ──


def _get_clipboard_text() -> str | None:
    """Read current clipboard text (CF_UNICODETEXT). Returns None if empty."""
    if not user32.OpenClipboard(0):
        return None
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return None
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def _set_clipboard_text(text: str) -> bool:
    """Write text to clipboard as CF_UNICODETEXT."""
    if not user32.OpenClipboard(0):
        return False
    try:
        user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            kernel32.GlobalFree(handle)
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        user32.SetClipboardData(CF_UNICODETEXT, handle)
        return True
    finally:
        user32.CloseClipboard()


def clipboard_paste(text: str):
    """Paste text via clipboard (Ctrl+V), preserving original clipboard content."""
    # Save original clipboard
    original = _get_clipboard_text()

    # Write our text
    if not _set_clipboard_text(text):
        logger.warning("Failed to set clipboard, falling back to KEYEVENTF_UNICODE")
        for ch in text:
            _type_unicode_char(ch)
        return

    # Ctrl+V
    _send_key(vk=VK_CONTROL)
    time.sleep(random.uniform(0.02, 0.04))
    _press_release_vk(WIN_VK["v"])
    time.sleep(random.uniform(0.02, 0.04))
    _send_key(vk=VK_CONTROL, flags=KEYEVENTF_KEYUP)

    # Wait for paste to be processed by target application
    time.sleep(random.uniform(0.05, 0.12))

    # Restore original clipboard
    if original is not None:
        _set_clipboard_text(original)
    else:
        # Clear clipboard to original empty state
        if user32.OpenClipboard(0):
            user32.EmptyClipboard()
            user32.CloseClipboard()


# ── Public API ──


def type_text(text: str):
    r"""Type text using segmented input strategy (standalone, no humanize).

    - ``\n`` → Enter VK, ``\t`` → Tab VK, ``\r`` → skipped
    - ASCII printable → VK physical key (with per-segment IME toggle)
    - Non-ASCII → per-character IME composition or KEYEVENTF_UNICODE fallback

    Note: When called via NativeActionBackend, the backend adds humanize
    delays.  This standalone function includes its own IME management.
    """
    ime_was_chinese = _is_ime_chinese_mode()
    segments = _split_text(text)

    for kind, segment in segments:
        if kind == "control":
            for char in segment:
                if char == "\n":
                    _press_release_vk(WIN_VK["return"])
                elif char == "\t":
                    _press_release_vk(WIN_VK["tab"])
                # \r is silently skipped (CR in CRLF; \n handles Enter)
        elif kind == "ascii":
            ime_ok = _ensure_ime_english()
            if ime_ok:
                for char in segment:
                    type_char_vk(char)
            else:
                for char in segment:
                    _type_unicode_char(char)
        elif kind == "non_ascii":
            for char in segment:
                if not ime_compose(char):
                    _type_unicode_char(char)

    # Restore original IME state
    if ime_was_chinese:
        _restore_ime_chinese()
    elif _is_ime_chinese_mode():
        _ensure_ime_english()


def _split_text(text: str) -> list[tuple[str, str]]:
    """Split text into contiguous segments of (kind, content).

    Kinds: 'control' (\\n, \\t), 'ascii' (printable ASCII), 'non_ascii' (everything else).
    """
    if not text:
        return []

    segments: list[tuple[str, str]] = []
    current_kind = _char_kind(text[0])
    current_chars = [text[0]]

    for char in text[1:]:
        kind = _char_kind(char)
        if kind == current_kind:
            current_chars.append(char)
        else:
            segments.append((current_kind, "".join(current_chars)))
            current_kind = kind
            current_chars = [char]

    segments.append((current_kind, "".join(current_chars)))
    return segments


def _char_kind(char: str) -> str:
    if char in ("\n", "\t", "\r"):
        return "control"
    if 0x20 <= ord(char) <= 0x7E:
        return "ascii"
    return "non_ascii"


def hotkey(combo: str):
    """Hotkey combo: 'ctrl+a', 'ctrl+shift+s', 'alt+f4'."""
    keys = [k.strip().lower() for k in combo.split("+")]

    mod_vks = []
    final_vk = None

    for key in keys:
        if key in WIN_MOD_VK:
            mod_vks.append(WIN_MOD_VK[key])
        elif key in WIN_VK:
            final_vk = WIN_VK[key]
        else:
            raise ValueError(f"Unknown key: '{key}'")

    if final_vk is None:
        raise ValueError("Hotkey must include a non-modifier key")

    # Press modifiers
    for vk in mod_vks:
        _send_key(vk=vk)
        time.sleep(random.uniform(0.02, 0.04))

    # Press+release final key
    _press_release_vk(final_vk)

    # Release modifiers (reverse order)
    for vk in reversed(mod_vks):
        _send_key(vk=vk, flags=KEYEVENTF_KEYUP)
        time.sleep(random.uniform(0.02, 0.04))
