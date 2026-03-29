"""GPU / device configuration for the perception engine — Windows CUDA only."""

from dataclasses import dataclass

from xclaw.platform.detect import detect_platform


@dataclass
class PerceptionConfig:
    """Hardware configuration for the perception engine."""
    yolo_device: str            # "cuda" | "cpu"
    yolo_onnx_ep: str           # ONNX Execution Provider
    yolo_trt_enabled: bool      # Whether to try TensorRT EP first
    classifier_device: str      # "cuda" | "cpu"
    classifier_enabled: bool
    ocr_use_gpu: bool
    ocr_det_limit: int          # max input image side length

    def describe(self) -> str:
        lines = [
            f"YOLO: {self.yolo_device} ({self.yolo_onnx_ep}, TRT={self.yolo_trt_enabled})",
            f"Classifier: {self.classifier_device}, enabled={self.classifier_enabled}",
            f"OCR: {'GPU' if self.ocr_use_gpu else 'CPU'}, det_limit={self.ocr_det_limit}",
        ]
        return "\n".join(lines)


def build_perception_config() -> PerceptionConfig:
    """Build optimal perception config for the current platform."""
    plat = detect_platform()

    # ── Windows + CUDA ──
    if plat.gpu_backend == "cuda":
        return PerceptionConfig(
            yolo_device="cuda",
            yolo_onnx_ep="CUDAExecutionProvider",
            yolo_trt_enabled=True,
            classifier_device="cuda",
            classifier_enabled=True,
            ocr_use_gpu=True,                # CUDA via onnxruntime-gpu (RapidOCR)
            ocr_det_limit=960,
        )

    # ── Fallback: CPU ──
    return PerceptionConfig(
        yolo_device="cpu",
        yolo_onnx_ep="CPUExecutionProvider",
        yolo_trt_enabled=False,
        classifier_device="cpu",
        classifier_enabled=True,
        ocr_use_gpu=False,
        ocr_det_limit=640,
    )
