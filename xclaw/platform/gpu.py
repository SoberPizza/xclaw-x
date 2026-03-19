"""GPU / device configuration for the perception engine."""

from dataclasses import dataclass

from xclaw.platform.detect import detect_platform


@dataclass
class PerceptionConfig:
    """Hardware configuration for the perception engine."""
    yolo_device: str            # "cuda" | "mps" | "cpu"
    yolo_onnx_ep: str           # ONNX Execution Provider
    florence2_device: str       # "cuda" | "cpu" (macOS cannot use mps)
    florence2_dtype: str        # "float16" | "float32"
    florence2_enabled: bool
    florence2_conditional: bool # only trigger for icons without text
    ocr_use_gpu: bool
    ocr_det_limit: int          # max input image side length

    def describe(self) -> str:
        lines = [
            f"YOLO: {self.yolo_device} ({self.yolo_onnx_ep})",
            f"Florence-2: {self.florence2_device} {self.florence2_dtype}",
            f"  enabled={self.florence2_enabled}, conditional={self.florence2_conditional}",
            f"OCR: {'GPU' if self.ocr_use_gpu else 'CPU'}, det_limit={self.ocr_det_limit}",
        ]
        return "\n".join(lines)


def build_perception_config() -> PerceptionConfig:
    """Build optimal perception config for the current platform."""
    plat = detect_platform()

    if not plat.supported:
        raise SystemError(plat.support_reason)

    # ── Windows + CUDA ──
    if plat.system == "Windows" and plat.gpu_backend == "cuda":
        return PerceptionConfig(
            yolo_device="cuda",
            yolo_onnx_ep="CUDAExecutionProvider",
            florence2_device="cuda",
            florence2_dtype="float16",
            florence2_enabled=True,
            florence2_conditional=True,
            ocr_use_gpu=True,
            ocr_det_limit=960,
        )

    # ── macOS Apple Silicon ──
    if plat.system == "Darwin" and plat.is_apple_silicon:
        return PerceptionConfig(
            yolo_device="mps",
            yolo_onnx_ep="CoreMLExecutionProvider",
            florence2_device="cpu",           # MPS gather bug, force CPU
            florence2_dtype="float32",        # CPU does not support FP16
            florence2_enabled=True,
            florence2_conditional=True,       # conditional invocation saves time
            ocr_use_gpu=False,               # PaddlePaddle macOS has no GPU
            ocr_det_limit=960,
        )

    # ── Fallback: CPU ──
    return PerceptionConfig(
        yolo_device="cpu",
        yolo_onnx_ep="CPUExecutionProvider",
        florence2_device="cpu",
        florence2_dtype="float32",
        florence2_enabled=True,
        florence2_conditional=True,
        ocr_use_gpu=False,
        ocr_det_limit=640,
    )
