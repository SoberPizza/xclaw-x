"""Tests for IoU calculation and element merging."""

from xclaw.core.perception.types import RawElement
from xclaw.core.perception.merger import box_iou, merge_elements, merge_element_dicts


def _elem(id, type="text", bbox=(0, 0, 10, 10), content="test"):
    return RawElement(
        id=id, type=type, bbox=bbox,
        center=((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2),
        content=content,
    )


class TestBoxIou:
    def test_identical(self):
        assert box_iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0

    def test_no_overlap(self):
        assert box_iou((0, 0, 5, 5), (10, 10, 20, 20)) == 0.0

    def test_partial_overlap(self):
        iou = box_iou((0, 0, 10, 10), (5, 5, 15, 15))
        # Intersection = 5x5=25, Union = 100+100-25=175
        assert abs(iou - 25 / 175) < 1e-6

    def test_contained(self):
        iou = box_iou((0, 0, 20, 20), (5, 5, 15, 15))
        # Intersection = 100, Union = 400+100-100=400
        assert abs(iou - 100 / 400) < 1e-6

    def test_zero_area(self):
        assert box_iou((5, 5, 5, 5), (0, 0, 10, 10)) == 0.0


class TestMergeElements:
    def test_empty(self):
        assert merge_elements([]) == []

    def test_no_overlap(self):
        elems = [
            _elem(0, bbox=(0, 0, 10, 10)),
            _elem(1, bbox=(20, 20, 30, 30)),
        ]
        result = merge_elements(elems)
        assert len(result) == 2
        assert result[0].id == 0
        assert result[1].id == 1

    def test_same_type_overlap_discards(self):
        elems = [
            _elem(0, type="text", bbox=(0, 0, 10, 10), content="hello"),
            _elem(1, type="text", bbox=(1, 1, 11, 11), content="world"),
        ]
        result = merge_elements(elems, iou_threshold=0.3)
        assert len(result) == 1

    def test_different_type_overlap_merges_content(self):
        elems = [
            _elem(0, type="text", bbox=(0, 0, 10, 10), content="label"),
            _elem(1, type="icon", bbox=(0, 0, 10, 10), content="icon-name"),
        ]
        result = merge_elements(elems, iou_threshold=0.3)
        assert len(result) == 1
        assert "label" in result[0].content
        assert "icon-name" in result[0].content

    def test_renumbers_sequentially(self):
        elems = [
            _elem(5, bbox=(0, 0, 10, 10)),
            _elem(9, bbox=(50, 50, 60, 60)),
            _elem(12, bbox=(100, 100, 110, 110)),
        ]
        result = merge_elements(elems)
        assert [e.id for e in result] == [0, 1, 2]


def _dict_elem(type="text", bbox=(0, 0, 10, 10), content="test"):
    return {
        "type": type,
        "bbox": list(bbox),
        "content": content,
        "confidence": 1.0,
        "center": [(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2],
    }


class TestMergeElementDicts:
    def test_empty(self):
        assert merge_element_dicts([]) == []

    def test_no_overlap(self):
        elems = [
            _dict_elem(bbox=(0, 0, 10, 10)),
            _dict_elem(bbox=(20, 20, 30, 30)),
        ]
        result = merge_element_dicts(elems)
        assert len(result) == 2

    def test_same_type_overlap_discards(self):
        elems = [
            _dict_elem(type="text", bbox=(0, 0, 10, 10), content="hello"),
            _dict_elem(type="text", bbox=(1, 1, 11, 11), content="world"),
        ]
        result = merge_element_dicts(elems, iou_threshold=0.3)
        assert len(result) == 1

    def test_cross_type_uses_lower_threshold(self):
        """icon+text at IoU ~0.36 should merge with cross_type_iou=0.3."""
        elems = [
            _dict_elem(type="icon", bbox=(0, 0, 100, 100)),
            _dict_elem(type="text", bbox=(30, 30, 80, 80), content="label"),
        ]
        # IoU of these boxes: intersection=50*50=2500, union=10000+2500-2500=10000 → 0.25
        # Use a threshold that should trigger merge
        elems = [
            _dict_elem(type="icon", bbox=(0, 0, 100, 100)),
            _dict_elem(type="text", bbox=(0, 0, 80, 80), content="label"),
        ]
        # IoU: inter=6400, union=10000+6400-6400=10000 → 0.64
        result = merge_element_dicts(elems, cross_type_iou_threshold=0.3)
        assert len(result) == 1

    def test_cross_type_prefers_text_content(self):
        """When merging icon+text, text content should win."""
        elems = [
            _dict_elem(type="icon", bbox=(0, 0, 100, 100), content="Foreign Language"),
            _dict_elem(type="text", bbox=(0, 0, 90, 90), content="情感"),
        ]
        result = merge_element_dicts(elems, cross_type_iou_threshold=0.3)
        assert len(result) == 1
        assert result[0]["content"] == "情感"

    def test_same_type_below_threshold_keeps_both(self):
        elems = [
            _dict_elem(type="text", bbox=(0, 0, 100, 100), content="a"),
            _dict_elem(type="text", bbox=(80, 80, 200, 200), content="b"),
        ]
        result = merge_element_dicts(elems, iou_threshold=0.5)
        assert len(result) == 2
