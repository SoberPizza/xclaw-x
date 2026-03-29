"""OCR engine — RapidOCR (PPOCRv5 mobile ONNX) on CUDA."""

import numpy as np

from xclaw.core.perception.types import TextBox


class OCREngine:
    """RapidOCR PPOCRv5 mobile — Chinese/English bilingual, CUDA via onnxruntime-gpu.

    Replaces the old PaddleOCR + paddlepaddle CPU combo (85s → ~200ms on GPU).
    Models are auto-downloaded on first use by RapidOCR.
    """

    def __init__(self, use_gpu: bool = True, det_limit: int = 960):
        # Ensure CUDA DLLs are discoverable before onnxruntime creates sessions
        if use_gpu:
            self._register_cuda_dlls()

        from rapidocr import RapidOCR, EngineType, LangRec, ModelType
        from rapidocr.utils.typings import OCRVersion

        params = {
            "Det.engine_type": EngineType.ONNXRUNTIME,
            "Det.ocr_version": OCRVersion.PPOCRV5,
            "Det.model_type": ModelType.MOBILE,
            "Rec.engine_type": EngineType.ONNXRUNTIME,
            "Rec.lang_type": LangRec.CH,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.model_type": ModelType.MOBILE,
        }
        if use_gpu:
            params["EngineConfig.onnxruntime.use_cuda"] = True

        self.engine = RapidOCR(params=params)
        self._det_limit = det_limit

    @staticmethod
    def _register_cuda_dlls():
        """Register nvidia DLL directories so onnxruntime can find CUDA libs."""
        import os
        import site

        for sp in site.getsitepackages():
            nvidia_dir = os.path.join(sp, "nvidia")
            if not os.path.isdir(nvidia_dir):
                continue
            for sub in os.listdir(nvidia_dir):
                bin_dir = os.path.join(nvidia_dir, sub, "bin")
                if os.path.isdir(bin_dir):
                    try:
                        os.add_dll_directory(bin_dir)
                    except OSError:
                        pass

        # Pre-load torch to register CUDA runtime
        try:
            import torch  # noqa: F401
        except Exception:
            pass

    def detect(self, image: np.ndarray, min_confidence: float = 0.6) -> list[TextBox]:
        result = self.engine(image, use_det=True, use_cls=False, use_rec=True)
        boxes: list[TextBox] = []
        if result.boxes is None:
            return boxes

        for polygon, text, score in zip(result.boxes, result.txts, result.scores):
            if score < min_confidence:
                continue
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            poly_list = [list(p) for p in polygon]
            boxes.append(TextBox(
                bbox=(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))),
                text=str(text).strip(),
                confidence=round(float(score), 3),
                polygon=poly_list,
            ))
        return boxes
