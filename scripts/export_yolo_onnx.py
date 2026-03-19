#!/usr/bin/env python3
"""Export YOLO icon_detect model from .pt to .onnx format.

Usage:
    uv run python scripts/export_yolo_onnx.py

Requires: ultralytics
Output: models/icon_detect/model.onnx
"""

from pathlib import Path


def main():
    models_dir = Path(__file__).parent.parent / "models"
    pt_path = models_dir / "icon_detect" / "model.pt"

    if not pt_path.exists():
        # Try weights/ fallback
        pt_path = Path(__file__).parent.parent / "weights" / "icon_detect" / "model.pt"

    if not pt_path.exists():
        print(f"❌ YOLO model not found at {pt_path}")
        print("   Run: uv run python scripts/download_models.py")
        return

    print(f"Loading YOLO model from {pt_path}...")

    from ultralytics import YOLO

    model = YOLO(str(pt_path))

    onnx_path = pt_path.parent / "model.onnx"
    print(f"Exporting to {onnx_path}...")

    model.export(
        format="onnx",
        imgsz=640,
        simplify=True,
        opset=17,
    )

    if onnx_path.exists():
        mb = onnx_path.stat().st_size / (1024 * 1024)
        print(f"✅ ONNX export complete: {mb:.1f} MB")
    else:
        # ultralytics may put it next to the .pt with different name
        exported = list(pt_path.parent.glob("*.onnx"))
        if exported:
            exported[0].rename(onnx_path)
            mb = onnx_path.stat().st_size / (1024 * 1024)
            print(f"✅ ONNX export complete: {mb:.1f} MB")
        else:
            print("❌ ONNX export failed — no .onnx file produced")


if __name__ == "__main__":
    main()
