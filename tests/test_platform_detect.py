"""Platform detection tests — Windows CUDA only."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from xclaw.platform.detect import PlatformInfo, detect_platform, _get_memory_gb, _detect_gpu_backend
from xclaw.platform.gpu import PerceptionConfig, build_perception_config


# ---------------------------------------------------------------------------
# PlatformInfo dataclass
# ---------------------------------------------------------------------------


class TestPlatformInfo:
    def test_windows_cuda(self):
        info = PlatformInfo(
            system="Windows", arch="AMD64",
            memory_gb=32, gpu_backend="cuda",
        )
        assert info.system == "Windows"
        assert info.gpu_backend == "cuda"

    def test_frozen(self):
        info = PlatformInfo(
            system="Windows", arch="AMD64",
            memory_gb=16, gpu_backend="cuda",
        )
        with pytest.raises(AttributeError):
            info.system = "Linux"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# _detect_gpu_backend()
# ---------------------------------------------------------------------------


class TestDetectGPUBackend:
    def test_with_cuda(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = _detect_gpu_backend()
        assert result == "cuda"

    def test_no_cuda(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = _detect_gpu_backend()
        assert result == "cpu"


# ---------------------------------------------------------------------------
# PerceptionConfig
# ---------------------------------------------------------------------------


class TestPerceptionConfig:
    def test_describe_output(self):
        cfg = PerceptionConfig(
            yolo_device="cuda",
            yolo_onnx_ep="CUDAExecutionProvider",
            yolo_trt_enabled=True,
            classifier_device="cuda",
            classifier_enabled=True,
            ocr_use_gpu=False,
            ocr_det_limit=960,
        )
        desc = cfg.describe()
        assert "YOLO" in desc
        assert "Classifier" in desc
        assert "OCR" in desc
        assert "TRT=True" in desc


# ---------------------------------------------------------------------------
# build_perception_config()
# ---------------------------------------------------------------------------


class TestBuildPerceptionConfig:
    @patch("xclaw.platform.gpu.detect_platform")
    def test_windows_cuda(self, mock_detect):
        mock_detect.return_value = PlatformInfo(
            system="Windows", arch="AMD64",
            memory_gb=32, gpu_backend="cuda",
        )
        cfg = build_perception_config()
        assert cfg.yolo_device == "cuda"
        assert cfg.yolo_onnx_ep == "CUDAExecutionProvider"
        assert cfg.yolo_trt_enabled is True
        assert cfg.classifier_device == "cuda"
        assert cfg.ocr_use_gpu is True

    @patch("xclaw.platform.gpu.detect_platform")
    def test_cpu_fallback(self, mock_detect):
        mock_detect.return_value = PlatformInfo(
            system="Windows", arch="AMD64",
            memory_gb=32, gpu_backend="cpu",
        )
        cfg = build_perception_config()
        assert cfg.yolo_device == "cpu"
        assert cfg.yolo_onnx_ep == "CPUExecutionProvider"
        assert cfg.yolo_trt_enabled is False
        assert cfg.ocr_det_limit == 640
