"""PaddleOCR engine — cross-platform (GPU on Windows, CPU+MKL-DNN on macOS)."""

import numpy as np

from xclaw.core.perception.types import TextBox


class OCREngine:
    """PaddleOCR v4 mobile — Chinese/English bilingual.

    Windows: GPU accelerated
    macOS:   CPU + MKL-DNN (Apple Silicon CPU is fast enough)
    """

    def __init__(self, use_gpu: bool = False, det_limit: int = 960):
        from paddleocr import PaddleOCR

        self.engine = PaddleOCR(
            use_textline_orientation=True,
            lang="ch",
            text_det_limit_side_len=det_limit,
            device="cpu" if not use_gpu else "gpu",
        )

        # PaddleX's setup_logging() forces its own colored StreamHandler during
        # PaddleOCR init.  Strip all handlers so CLI output stays clean JSON.
        import logging as _logging
        _pdx = _logging.getLogger("paddlex")
        _pdx.handlers.clear()
        _pdx.addHandler(_logging.NullHandler())
        _pdx.propagate = False

    def detect(self, image: np.ndarray, min_confidence: float = 0.6) -> list[TextBox]:
        results = list(self.engine.predict(image))
        if not results:
            return []

        r = results[0]
        polys = r["dt_polys"]
        texts = r["rec_texts"]
        scores = r["rec_scores"]

        boxes = []
        for polygon, text, confidence in zip(polys, texts, scores):
            if confidence < min_confidence:
                continue
            poly_list = polygon.tolist() if hasattr(polygon, "tolist") else polygon
            xs = [p[0] for p in poly_list]
            ys = [p[1] for p in poly_list]
            boxes.append(TextBox(
                bbox=(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))),
                text=text.strip(),
                confidence=round(confidence, 3),
                polygon=poly_list,
            ))
        return boxes
