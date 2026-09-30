import pytest

from defect_logger.verdict import (
    InvalidSampleSize,
    InvalidSeverity,
    compute_verdict,
    limits_for,
)


# The six cases from the brief.
@pytest.mark.parametrize(
    "sample_size, severities, expected",
    [
        (40, ["major"] * 3, "ACCEPT"),  # 1
        (40, ["major"] * 4, "REJECT"),  # 2
        (39, ["major"] * 3, "REJECT"),  # 3 (10 row: major limit 1)
        (149, ["major"] * 6, "REJECT"),  # 4 (40 row: major limit 3)
        (150, ["major"] * 6, "ACCEPT"),  # 5 (150 row: major limit 6)
        (60, ["critical"], "REJECT"),  # 6
    ],
)
def test_brief_cases(sample_size, severities, expected):
    assert compute_verdict(sample_size, severities) == expected


def test_zero_defects_is_accept():  # R3
    assert compute_verdict(40, []) == "ACCEPT"


@pytest.mark.parametrize("bad", [0, -1, -100, 1.5, "40", None, True])
def test_invalid_sample_size_refuses_verdict(bad):  # R4
    with pytest.raises(InvalidSampleSize):
        compute_verdict(bad, [])


# R1: row selection, no interpolation.
@pytest.mark.parametrize(
    "sample_size, expected",
    [
        (1, (0, 1)),
        (9, (0, 1)),
        (10, (1, 3)),
        (39, (1, 3)),
        (40, (3, 6)),  # exactly on the row -> that row, not the one below
        (100, (3, 6)),
        (149, (3, 6)),
        (150, (6, 12)),
        (599, (6, 12)),
        (600, (12, 25)),
        (900, (12, 25)),
    ],
)
def test_limits_for(sample_size, expected):
    assert limits_for(sample_size) == expected


# R2: "greater than", so exactly on the limit is fine.
@pytest.mark.parametrize(
    "sample_size, severities, expected",
    [
        (40, ["minor"] * 6, "ACCEPT"),
        (40, ["minor"] * 7, "REJECT"),
        (1, ["minor"], "ACCEPT"),
        (1, ["minor"] * 2, "REJECT"),
        (1, ["major"], "REJECT"),  # major limit is 0 on the first row
        (600, ["major"] * 12 + ["minor"] * 25, "ACCEPT"),
        (600, ["major"] * 12 + ["minor"] * 26, "REJECT"),
    ],
)
def test_limit_boundaries(sample_size, severities, expected):
    assert compute_verdict(sample_size, severities) == expected


def test_critical_rejects_even_with_huge_sample():
    assert compute_verdict(10000, ["critical"]) == "REJECT"


def test_unknown_severity_is_rejected():
    with pytest.raises(InvalidSeverity):
        compute_verdict(40, ["urgent"])