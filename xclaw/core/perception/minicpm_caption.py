"""MiniCPM-V 2.0 icon caption — replaces Florence-2.

No transformers upper-bound constraint.

Windows: CUDA FP16  (~200ms/icon)
macOS:   CPU FP32   (~2-3s/icon)
"""

from pathlib import Path

import numpy as np
import torch


def _patch_minicpmv_decode(model):
    """Fix MiniCPM-V _decode for torch>=2.6 / transformers>=4.44.

    The original ``_decode`` passes only ``inputs_embeds`` to
    ``self.llm.generate()`` without ``attention_mask``.  Without an
    attention mask, ``prepare_inputs_for_generation`` cannot construct
    ``position_ids``, so the rotary-embedding cosine lookup receives
    empty tensors.

    The fix: build a proper ``attention_mask`` from the embedding shape
    so the LLM can derive ``position_ids`` throughout generation.
    """
    orig_decode = model._decode

    def _patched_decode(inputs_embeds, tokenizer, **kwargs):
        batch, seq_len, _ = inputs_embeds.shape
        attention_mask = torch.ones(
            batch, seq_len, dtype=torch.long, device=inputs_embeds.device
        )
        return orig_decode(
            inputs_embeds,
            tokenizer,
            attention_mask=attention_mask,
            **kwargs,
        )

    model._decode = _patched_decode


class MiniCPMCaption:
    """Generate short UI-element descriptions using MiniCPM-V 2.0."""

    def __init__(self, model_dir: Path, device: str = "cpu", dtype=torch.float32):
        from transformers import AutoModel, AutoTokenizer
        import transformers
        transformers.logging.set_verbosity_error()

        self.device = device
        self.dtype = dtype

        self.tokenizer = AutoTokenizer.from_pretrained(
            str(model_dir), trust_remote_code=True
        )
        self.model = AutoModel.from_pretrained(
            str(model_dir),
            torch_dtype=dtype,
            trust_remote_code=True,
        ).to(device).eval()

        _patch_minicpmv_decode(self.model)

    @torch.inference_mode()
    def batch_caption(
        self, screenshot: np.ndarray, icon_elements: list[dict]
    ) -> list[str]:
        """Generate semantic descriptions for icon regions.

        Args:
            screenshot: Full screenshot as numpy array (RGB).
            icon_elements: Elements needing caption (must have ``bbox`` key).

        Returns:
            List of text descriptions, one per element.
        """
        from PIL import Image

        captions = []
        pil_img = Image.fromarray(screenshot)

        for elem in icon_elements:
            x1, y1, x2, y2 = elem["bbox"]
            crop = pil_img.crop((
                max(0, x1 - 5), max(0, y1 - 5),
                min(pil_img.width, x2 + 5), min(pil_img.height, y2 + 5),
            ))

            try:
                msgs = [{"role": "user", "content": "Describe this UI element in a few words."}]
                answer, _ = self.model.chat(
                    image=crop,
                    msgs=msgs,
                    context=None,
                    tokenizer=self.tokenizer,
                    sampling=False,
                    max_new_tokens=30,
                )
                captions.append(answer.strip())
            except Exception:
                captions.append("")

        return captions
