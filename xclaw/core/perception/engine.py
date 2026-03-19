"""Perception engine — platform-adaptive orchestrator.

Windows:  YOLO(CUDA) + PaddleOCR(GPU) + Florence-2(CUDA FP16)
macOS:    YOLO(MPS)  + PaddleOCR(CPU) + Florence-2(CPU FP32)
"""

import sys
import time
import base64
import io
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from xclaw.config import PERCEPTION_CONFIG, MODELS_DIR, WEIGHTS_DIR
from xclaw.core.perception.ocr import OCREngine
from xclaw.core.perception.omniparser import OmniDetector, OmniCaption
from xclaw.core.perception.merger import fuse_results


class PerceptionEngine:
    """Perception engine — platform-adaptive.

    Windows:  YOLO(CUDA) + PaddleOCR(GPU) + Florence-2(CUDA FP16)
    macOS:    YOLO(MPS)  + PaddleOCR(CPU) + Florence-2(CPU FP32)
    """

    _instance: Optional["PerceptionEngine"] = None

    @classmethod
    def get_instance(cls) -> "PerceptionEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.config = PERCEPTION_CONFIG
        self._models_loaded = False
        self._detector: Optional[OmniDetector] = None
        self._caption: Optional[OmniCaption] = None
        self._ocr: Optional[OCREngine] = None

    def _ensure_models(self):
        """Lazy-load all models."""
        if self._models_loaded:
            return

        t0 = time.time()
        model_dir = self._find_model_dir()

        # 1. YOLO icon_detect
        onnx_path = model_dir / "icon_detect" / "model.onnx"
        pt_path = model_dir / "icon_detect" / "model.pt"

        if onnx_path.exists():
            self._detector = OmniDetector.from_onnx(
                str(onnx_path),
                provider=self.config.yolo_onnx_ep,
            )
        elif pt_path.exists():
            self._detector = OmniDetector.from_ultralytics(
                str(pt_path),
                device=self.config.yolo_device,
            )
        else:
            raise FileNotFoundError(
                f"No YOLO model found at {model_dir / 'icon_detect'}. "
                "Run: uv run python scripts/download_models.py"
            )

        # 2. PaddleOCR
        self._ocr = OCREngine(
            use_gpu=self.config.ocr_use_gpu,
            det_limit=self.config.ocr_det_limit,
        )

        # 3. Florence-2 (conditional)
        if self.config.florence2_enabled:
            florence_dir = model_dir / "icon_caption_florence"
            if florence_dir.exists():
                dtype = (
                    torch.float16
                    if self.config.florence2_dtype == "float16"
                    else torch.float32
                )
                self._caption = OmniCaption(
                    model_dir=florence_dir,
                    device=self.config.florence2_device,
                    dtype=dtype,
                )

        self._models_loaded = True
        elapsed = time.time() - t0
        print(f"[engine] Models loaded in {elapsed:.1f}s\n{self.config.describe()}")

    def full_look(
        self,
        region: Optional[list[int]] = None,
        with_image: bool = False,
    ) -> dict:
        """Full perception pipeline:

        1. Screenshot
        2. YOLO detect interactive regions
        3. PaddleOCR extract Chinese/English text
        4. Spatial fusion + dedup
        5. Conditional Florence-2 for text-less icons
        6. Assign global IDs
        """
        self._ensure_models()

        t_start = time.time()

        # Step 1: Screenshot
        screenshot = self._capture(region=region)
        t_capture = time.time()

        # Step 2: YOLO detection
        icon_boxes = self._detector.detect(screenshot)
        t_yolo = time.time()

        # Step 3: PaddleOCR
        text_boxes = self._ocr.detect(screenshot)
        t_ocr = time.time()

        # Step 4: Spatial fusion
        merged, icons_needing_caption = fuse_results(icon_boxes, text_boxes)
        t_merge = time.time()

        # Step 5: Conditional Florence-2 caption
        if (
            self.config.florence2_enabled
            and self._caption is not None
            and icons_needing_caption
        ):
            captions = self._caption.batch_caption(screenshot, icons_needing_caption)
            for elem, cap in zip(icons_needing_caption, captions):
                elem["content"] = cap
        t_caption = time.time()

        # Step 6: Assign sequential IDs
        for i, elem in enumerate(merged, start=1):
            elem["id"] = i

        h, w = screenshot.shape[:2]

        result = {
            "status": "ok",
            "element_count": len(merged),
            "elements": merged,
            "resolution": [w, h],
            "timing": {
                "capture_ms": round((t_capture - t_start) * 1000),
                "yolo_ms": round((t_yolo - t_capture) * 1000),
                "ocr_ms": round((t_ocr - t_yolo) * 1000),
                "merge_ms": round((t_merge - t_ocr) * 1000),
                "caption_ms": round((t_caption - t_merge) * 1000),
                "total_ms": round((t_caption - t_start) * 1000),
            },
        }

        if with_image:
            result["image_b64"] = self._encode_image(screenshot)

        return result

    def screenshot_only(self, region=None) -> dict:
        """Pure screenshot, no perception."""
        screenshot = self._capture(region=region)
        return {
            "status": "ok",
            "image_b64": self._encode_image(screenshot),
        }

    @staticmethod
    def _capture(region=None) -> np.ndarray:
        """Capture screen as numpy array (RGB)."""
        import mss
        from PIL import Image

        with mss.mss() as sct:
            if region:
                x, y, w, h = region
                monitor = {"left": x, "top": y, "width": w, "height": h}
            else:
                monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        return np.array(img)

    @staticmethod
    def _encode_image(img: np.ndarray) -> str:
        from PIL import Image

        pil_img = Image.fromarray(img)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    @staticmethod
    def _find_model_dir() -> Path:
        candidates = [
            MODELS_DIR,                                      # models/ (new)
            WEIGHTS_DIR,                                     # weights/ (legacy)
            Path(__file__).parents[2] / "models",            # relative
            Path.home() / ".xclaw" / "models",               # user install
        ]
        for p in candidates:
            if (p / "icon_detect").exists():
                return p
        raise FileNotFoundError(
            "Model directory not found. Run: uv run python scripts/download_models.py"
        )
