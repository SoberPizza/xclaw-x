"""Shared fixtures for tests."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from xclaw.core.perception.types import RawElement
from xclaw.core.pipeline import PipelineResult

# ── Directories ──

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "screenshots"


# ── Helpers ──

def _elem(
    id: int,
    type: str = "text",
    bbox: tuple[int, int, int, int] = (0, 0, 100, 20),
    content: str = "test",
    confidence: float = 1.0,
    source: str = "",
) -> RawElement:
    return RawElement(
        id=id,
        type=type,
        bbox=bbox,
        center=((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2),
        content=content,
        confidence=confidence,
        source=source,
    )


def _build_elements(n: int = 10, resolution: tuple[int, int] = (1920, 1080)) -> list[RawElement]:
    """Build a grid of synthetic elements spread across the resolution."""
    w, h = resolution
    elems = []
    cols = 5
    for i in range(n):
        col = i % cols
        row = i // cols
        x1 = col * (w // cols) + 10
        y1 = row * 40 + 10
        x2 = x1 + 120
        y2 = y1 + 20
        elems.append(_elem(i, bbox=(x1, y1, x2, y2), content=f"item_{i}"))
    return elems


# ── Fixtures ──

@pytest.fixture
def screenshot_paths():
    """Return sorted list of real screenshots from the screenshots/ dir."""
    paths = sorted(SCREENSHOTS_DIR.glob("screen_*.png"))
    if len(paths) < 2:
        pytest.skip("Need at least 2 screenshots in screenshots/ directory")
    return paths


@pytest.fixture
def screenshot_pair(screenshot_paths):
    """Return (path[0], path[1]) — two consecutive screenshots."""
    return (str(screenshot_paths[0]), str(screenshot_paths[1]))


# ── Synthetic image helpers ──

@pytest.fixture
def make_gray_image(tmp_path):
    """Factory fixture: create a grayscale image of given size and color."""

    def _make(color: int, width: int = 1920, height: int = 1080, name: str = "img.png") -> str:
        img = np.full((height, width), color, dtype=np.uint8)
        path = str(tmp_path / name)
        cv2.imwrite(path, img)
        return path

    return _make


@pytest.fixture
def make_image_with_rect(tmp_path):
    """Factory: base color image with a filled rectangle."""

    def _make(
        bg_color: int = 128,
        rect_color: int = 255,
        rect: tuple[int, int, int, int] = (100, 100, 300, 200),
        width: int = 1920,
        height: int = 1080,
        name: str = "rect.png",
    ) -> str:
        img = np.full((height, width), bg_color, dtype=np.uint8)
        x1, y1, x2, y2 = rect
        img[y1:y2, x1:x2] = rect_color
        path = str(tmp_path / name)
        cv2.imwrite(path, img)
        return path

    return _make
