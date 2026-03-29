"""ConvNeXt-Tiny icon shape classifier (stub — model not yet trained)."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class IconClassifier:
    """ConvNeXt-Tiny fine-tuned icon shape classifier.

    This is a stub interface. The model is not yet trained.
    Once trained, load the checkpoint and implement inference logic.
    """

    def __init__(self, model_path: Path, device: str = "cuda"):
        self._model = None
        self._model_path = model_path
        self._device = device
        self._loaded = False

    def load(self) -> None:
        """Load the ConvNeXt-Tiny classification model."""
        if self._loaded:
            return
        if not self._model_path.exists():
            logger.info("Icon classifier model not found at %s, classification disabled", self._model_path)
            return
        # TODO: Load ConvNeXt-Tiny checkpoint when model is trained
        # import torch
        # from torchvision.models import convnext_tiny
        # self._model = convnext_tiny(num_classes=NUM_CLASSES)
        # self._model.load_state_dict(torch.load(self._model_path, map_location=self._device))
        # self._model.to(self._device).eval()
        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def classify(self, image: np.ndarray, icon_elements: list[dict]) -> list[str]:
        """Classify each icon bbox region, returning a class label per element."""
        if self._model is None:
            return ["unknown" for _ in icon_elements]

        # TODO: Implement inference when model is trained
        # 1. Crop each icon region from image using bbox
        # 2. Resize/normalize to model input size
        # 3. Batch inference
        # 4. Return predicted class labels
        return ["unknown" for _ in icon_elements]
