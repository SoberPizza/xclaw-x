"""Vision pipeline: delegates to PerceptionEngine and wraps result."""

from __future__ import annotations

from dataclasses import dataclass, field

from xclaw.core.perception.types import RawElement


@dataclass(slots=True)
class PipelineResult:
    """Full output of the vision pipeline."""

    elements: list[RawElement] = field(default_factory=list)
    resolution: tuple[int, int] = (0, 0)
    image_path: str = ""
    timing: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to the JSON format consumed by LLM."""
        return {
            "elements": [
                {
                    "id": e.id,
                    "type": e.type,
                    "bbox": list(e.bbox),
                    "center": list(e.center),
                    "content": e.content,
                }
                for e in self.elements
            ],
            "resolution": list(self.resolution),
            "timing": self.timing,
        }


def _dict_to_element(i: int, d: dict) -> RawElement:
    bbox = d["bbox"]
    if isinstance(bbox, list):
        bbox = tuple(bbox)
    center = d.get("center")
    if center:
        center = tuple(center)
    else:
        center = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
    return RawElement(
        id=i,
        type=d.get("type", "unknown"),
        bbox=bbox,
        center=center,
        content=d.get("content", ""),
        confidence=d.get("confidence", 1.0),
    )


def run_pipeline(image_path: str) -> PipelineResult:
    """Execute the vision pipeline by delegating to PerceptionEngine.

    Args:
        image_path: Path to screenshot image.

    Returns:
        PipelineResult wrapping the engine output.
    """
    from xclaw.core.perception.engine import PerceptionEngine

    engine = PerceptionEngine.get_instance()
    result = engine.full_look(from_image=image_path)

    elements = [
        _dict_to_element(i, d)
        for i, d in enumerate(result["elements"])
    ]
    w, h = result["resolution"]

    return PipelineResult(
        elements=elements,
        resolution=(w, h),
        image_path=image_path,
        timing=result.get("timing", {}),
    )
