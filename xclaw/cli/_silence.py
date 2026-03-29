"""Suppress third-party library noise for clean CLI output."""

import logging
import os


def silence_third_party():
    """Suppress all non-JSON output when running as CLI (for LLM consumption)."""
    # Python logging → CRITICAL only
    logging.getLogger().setLevel(logging.CRITICAL)

    # RapidOCR logging
    logging.getLogger("RapidOCR").setLevel(logging.CRITICAL)

    # Third-party env vars
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["YOLO_VERBOSE"] = "False"

    # ONNX Runtime (C++ layer) — 3=Error
    os.environ["ORT_LOG_LEVEL"] = "3"

    # transformers / huggingface_hub tqdm progress bars
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"


def ensure_cuda_dll_dirs():
    """Register nvidia DLL directories and pre-load torch for CUDA support."""
    import site

    for sp in site.getsitepackages():
        nvidia_dir = os.path.join(sp, "nvidia")
        if not os.path.isdir(nvidia_dir):
            continue
        for sub in os.listdir(nvidia_dir):
            bin_dir = os.path.join(nvidia_dir, sub, "bin")
            if os.path.isdir(bin_dir):
                os.add_dll_directory(bin_dir)

    try:
        import torch  # noqa: F401
    except Exception:
        pass
