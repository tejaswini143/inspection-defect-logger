import json

import pytest

from defect_logger import storage
from defect_logger.inspection import Inspection
from defect_logger.verdict import InvalidSampleSize, InvalidSeverity


def test_verdict_is_recomputed_as_defects_are_added():
    insp = Inspection("B-1", 40)
    assert insp.verdict() == "ACCEPT"  # zero defects
    for _ in range(3):
        insp.add_defect("major", "scratch")
    assert insp.verdict() == "ACCEPT"  # exactly on the limit
    insp.add_defect("major", "dent")
    assert insp.verdict() == "REJECT"


def test_severity_is_normalised():
    insp = Inspection("B-1", 40)
    insp.add_defect(" Major ", "  loose screw ")
    assert insp.defects == [{"severity": "major", "description": "loose screw"}]


def test_invalid_severity_and_description_are_refused():
    insp = Inspection("B-1", 40)
    with pytest.raises(InvalidSeverity):
        insp.add_defect("urgent", "x")
    with pytest.raises(ValueError):
        insp.add_defect("minor", "   ")
    assert insp.defects == []


@pytest.mark.parametrize("batch_id", ["", "   ", None])
def test_empty_batch_id_is_refused(batch_id):
    with pytest.raises(ValueError):
        Inspection(batch_id, 40)


def test_invalid_sample_size_is_refused():
    with pytest.raises(InvalidSampleSize):
        Inspection("B-1", 0)


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "i.json"
    insp = Inspection("B-9", 150)
    insp.add_defect("minor", "smudge")
    storage.save(insp, path)
    loaded = storage.load(path)
    assert loaded.to_dict() == insp.to_dict()


def test_load_missing_file_returns_none(tmp_path):
    assert storage.load(tmp_path / "nope.json") is None


def test_corrupt_json_gives_clear_error(tmp_path):
    path = tmp_path / "i.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load(path)


@pytest.mark.parametrize(
    "data",
    [
        {"batch_id": "B", "sample_size": 0, "defects": []},
        {"batch_id": "B", "sample_size": 40, "defects": [{"severity": "huge", "description": "x"}]},
        {"batch_id": "B", "sample_size": 40},
        [],
    ],
)
def test_hand_edited_bad_data_is_refused(tmp_path, data):
    path = tmp_path / "i.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(storage.StorageError):
        storage.load(path)