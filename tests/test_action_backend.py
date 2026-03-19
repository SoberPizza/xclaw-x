"""Action backend interface contract tests — no real mouse/keyboard events."""

from __future__ import annotations

import platform
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Platform router (__init__.py)
# ---------------------------------------------------------------------------


class TestPlatformRouter:
    def test_exports_all_symbols(self):
        """Verify __init__.py exports the required symbols."""
        from xclaw.action import __all__

        expected = {"click", "double_click", "scroll", "move_to", "type_text", "hotkey"}
        assert set(__all__) == expected

    def test_imports_resolve(self):
        """All public names should be importable."""
        from xclaw.action import click, double_click, scroll, move_to, type_text, hotkey

        assert callable(click)
        assert callable(double_click)
        assert callable(scroll)
        assert callable(move_to)
        assert callable(type_text)
        assert callable(hotkey)


# ---------------------------------------------------------------------------
# mouse.py high-level API
# ---------------------------------------------------------------------------


class TestMouseAPI:
    @patch("xclaw.action.click")
    @patch("xclaw.action.double_click")
    def test_click_returns_dict(self, mock_dbl, mock_click):
        from xclaw.action.mouse import click

        with patch("xclaw.action.mouse.HUMANIZE", False):
            result = click(100, 200, double=False)

        assert result["status"] == "ok"
        assert result["action"] == "click"
        assert result["x"] == 100
        assert result["y"] == 200
        assert result["double"] is False

    @patch("xclaw.action.click")
    @patch("xclaw.action.double_click")
    def test_double_click_returns_dict(self, mock_dbl, mock_click):
        from xclaw.action.mouse import click

        with patch("xclaw.action.mouse.HUMANIZE", False):
            result = click(300, 400, double=True)

        assert result["double"] is True

    @patch("xclaw.action.move_to")
    @patch("xclaw.action.scroll")
    def test_scroll_returns_dict(self, mock_scroll, mock_move):
        from xclaw.action.mouse import scroll

        with patch("xclaw.action.mouse.HUMANIZE", False):
            result = scroll("down", 3, 500, 500)

        assert result["status"] == "ok"
        assert result["action"] == "scroll"
        assert result["direction"] == "down"
        assert result["amount"] == 3


# ---------------------------------------------------------------------------
# keyboard.py high-level API
# ---------------------------------------------------------------------------


class TestKeyboardAPI:
    @patch("xclaw.action.type_text")
    def test_type_text_returns_dict(self, mock_type):
        from xclaw.action.keyboard import type_text

        with patch("xclaw.action.keyboard.HUMANIZE", False):
            result = type_text("Hello World")

        assert result["status"] == "ok"
        assert result["action"] == "type"
        assert result["text"] == "Hello World"

    @patch("xclaw.action.hotkey")
    def test_press_key_returns_dict(self, mock_hotkey):
        from xclaw.action.keyboard import press_key

        with patch("xclaw.action.keyboard.HUMANIZE", False):
            result = press_key("enter")

        assert result["status"] == "ok"
        assert result["action"] == "press"
        assert result["key"] == "enter"

    @patch("xclaw.action.hotkey")
    def test_press_combo_returns_dict(self, mock_hotkey):
        from xclaw.action.keyboard import press_key

        with patch("xclaw.action.keyboard.HUMANIZE", False):
            result = press_key("cmd+c")

        assert result["key"] == "cmd+c"
        mock_hotkey.assert_called_once_with("cmd+c")


# ---------------------------------------------------------------------------
# Darwin backend (only tested on macOS)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
class TestDarwinKeyboard:
    def test_mac_kc_has_common_keys(self):
        from xclaw.action.keyboard_darwin import MAC_KC

        for key in ["a", "z", "0", "9", "return", "tab", "space", "escape"]:
            assert key in MAC_KC, f"Missing key: {key}"

    def test_mac_mod_kc_has_modifiers(self):
        from xclaw.action.keyboard_darwin import MAC_MOD_KC

        for mod in ["cmd", "shift", "alt", "ctrl"]:
            assert mod in MAC_MOD_KC, f"Missing modifier: {mod}"

    def test_shift_chars_complete(self):
        from xclaw.action.keyboard_darwin import SHIFT_CHARS

        for char in "!@#$%^&*()_+{}|:\"<>?~":
            assert char in SHIFT_CHARS, f"Missing shift char: {char}"


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
class TestDarwinMouse:
    def test_screen_size_returns_tuple(self):
        from xclaw.action.mouse_darwin import _screen_size

        w, h = _screen_size()
        assert isinstance(w, int) and w > 0
        assert isinstance(h, int) and h > 0

    def test_cursor_pos_returns_tuple(self):
        from xclaw.action.mouse_darwin import _cursor_pos

        x, y = _cursor_pos()
        assert isinstance(x, int)
        assert isinstance(y, int)


# ---------------------------------------------------------------------------
# Windows backend (structure-only, runs on any platform via mock)
# ---------------------------------------------------------------------------


class TestWin32KeyboardStructure:
    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_win_vk_has_common_keys(self):
        from xclaw.action.keyboard_win32 import WIN_VK

        for key in ["a", "z", "0", "9", "return", "tab", "space", "escape"]:
            assert key in WIN_VK

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_win_mod_vk_has_modifiers(self):
        from xclaw.action.keyboard_win32 import WIN_MOD_VK

        for mod in ["ctrl", "shift", "alt"]:
            assert mod in WIN_MOD_VK


# ---------------------------------------------------------------------------
# humanize.py
# ---------------------------------------------------------------------------


class TestHumanize:
    def test_bezier_point_endpoints(self):
        from xclaw.action.humanize import bezier_point

        p0, p1, p2, p3 = (0, 0), (10, 10), (20, 20), (30, 30)

        # t=0 → start
        x, y = bezier_point(0.0, p0, p1, p2, p3)
        assert abs(x - p0[0]) < 1e-6
        assert abs(y - p0[1]) < 1e-6

        # t=1 → end
        x, y = bezier_point(1.0, p0, p1, p2, p3)
        assert abs(x - p3[0]) < 1e-6
        assert abs(y - p3[1]) < 1e-6

    def test_bezier_point_midpoint(self):
        from xclaw.action.humanize import bezier_point

        # Straight line control points → midpoint should be near (15, 15)
        p0, p3 = (0, 0), (30, 30)
        p1, p2 = (10, 10), (20, 20)

        x, y = bezier_point(0.5, p0, p1, p2, p3)
        assert 10 < x < 20
        assert 10 < y < 20
