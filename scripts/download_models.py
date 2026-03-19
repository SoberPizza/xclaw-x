#!/usr/bin/env python3
"""X-Claw cross-platform model downloader.

Total download: ~1.3 GB

macOS: uv run --extra mac python scripts/download_models.py
Win:   uv run --extra win python scripts/download_models.py
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

# Uncomment for Chinese users:
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

MODELS = Path(__file__).parent.parent / "models"


def main():
    MODELS.mkdir(exist_ok=True)

    print("=" * 60)
    print("  X-Claw Model Downloader")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Target:   {MODELS}")
    print("=" * 60)

    # 1. OmniParser V2
    _download_hf("microsoft/OmniParser-v2.0", [
        "icon_detect/model.pt",
        "icon_detect/model.yaml",
        "icon_detect/train_args.yaml",
        "icon_caption/config.json",
        "icon_caption/generation_config.json",
        "icon_caption/model.safetensors",
    ], "OmniParser V2 (~1.12 GB)")

    # Rename icon_caption → icon_caption_florence
    src = MODELS / "icon_caption"
    dst = MODELS / "icon_caption_florence"
    if src.exists() and not dst.exists():
        src.rename(dst)
        print(f"  Renamed {src.name} → {dst.name}")

    # 2. PaddleOCR
    print("\n📦 PaddleOCR v4 (auto-download on first use)")
    try:
        from paddleocr import PaddleOCR
        PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False, show_log=True)
        print("  ✅ PaddleOCR ready")
    except ImportError:
        print("  ⚠️  paddleocr not installed. Run: uv sync --extra mac (or --extra win)")

    # 3. Verify
    _verify()


def _download_hf(repo_id: str, files: list[str], label: str):
    print(f"\n📦 {label}")
    for f in files:
        print(f"  ↓ {f}")
        subprocess.run([
            sys.executable, "-m", "huggingface_hub", "download",
            repo_id, f, "--local-dir", str(MODELS),
        ], check=True)
    print("  ✅ Done")


def _verify():
    print("\n🔍 Verification:")
    checks = {
        "YOLO": MODELS / "icon_detect" / "model.pt",
        "Florence-2": MODELS / "icon_caption_florence" / "model.safetensors",
    }
    all_ok = True
    for name, path in checks.items():
        if path.exists():
            mb = path.stat().st_size / (1024 * 1024)
            print(f"  ✅ {name}: {mb:.1f} MB")
        else:
            print(f"  ❌ {name}: MISSING at {path}")
            all_ok = False

    if all_ok:
        print("\n✅ All models ready!")
    else:
        print("\n⚠️  Some models are missing. Check the output above.")


if __name__ == "__main__":
    main()
