"""PaddleOCR engine — cross-platform (GPU on Windows, CPU+MKL-DNN on macOS)."""

import platform

import numpy as np

from xclaw.core.perception.types import TextBox


class OCREngine:
    """PaddleOCR v4 mobile — Chinese/English bilingual.

    Windows: GPU accelerated
    macOS:   CPU + MKL-DNN (Apple Silicon CPU is fast enough)
    """

    def __init__(self, use_gpu: bool = False, det_limit: int = 960):
        from paddleocr import PaddleOCR

        is_mac = platform.system() == "Darwin"

        self.engine = PaddleOCR(
            use_angle_cls=True,
            lang="ch",                           # Chinese + English
            use_gpu=use_gpu and not is_mac,       # macOS force GPU off
            show_log=False,
            use_mp=False,
            enable_mkldnn=is_mac,                 # macOS enable MKL-DNN
            det_limit_side_len=det_limit,
            det_db_score_mode="slow",             # accuracy first
            rec_batch_num=16,
        )

    def detect(self, image: np.ndarray, min_confidence: float = 0.6) -> list[TextBox]:
        results = self.engine.ocr(image, cls=True)
        if not results or not results[0]:
            return []

        boxes = []
        for line in results[0]:
            polygon, (text, confidence) = line
            if confidence < min_confidence:
                continue
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            boxes.append(TextBox(
                bbox=(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))),
                text=text.strip(),
                confidence=round(confidence, 3),
                polygon=polygon,
            ))
        return boxes
