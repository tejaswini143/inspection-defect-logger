"""Verdict rule for a factory quality inspection.

Limits come from a table keyed by sample size (rules R1-R4 in the brief).
"""
from collections import Counter

SEVERITIES = ("critical", "major", "minor")

# (min sample size, major limit, minor limit), largest "at least" first.
LIMITS = (
    (600, 12, 25),
    (150, 6, 12),
    (40, 3, 6),
    (10, 1, 3),
    (1, 0, 1),
)


class InvalidSampleSize(ValueError):
    """Sample size is not a whole number >= 1."""


class InvalidSeverity(ValueError):
    """Severity is not critical, major or minor."""


def validate_sample_size(sample_size):
    # bool is a subclass of int; True is not a meaningful sample size.
    if isinstance(sample_size, bool) or not isinstance(sample_size, int):
        raise InvalidSampleSize(
            f"Sample size must be a whole number, got {sample_size!r}."
        )
    if sample_size < 1:
        raise InvalidSampleSize(f"Sample size must be at least 1, got {sample_size}.")
    return sample_size


def limits_for(sample_size):
    """R1: use the row with the largest 'at least' <= sample_size. No interpolation."""
    validate_sample_size(sample_size)
    for at_least, major_limit, minor_limit in LIMITS:
        if sample_size >= at_least:
            return major_limit, minor_limit


def compute_verdict(sample_size, severities):
    """Return 'ACCEPT' or 'REJECT' for a sample size and an iterable of severities.

    R2: REJECT if any critical, major > major limit, or minor > minor limit.
    R3: otherwise ACCEPT (including zero defects).
    R4: invalid sample size raises InvalidSampleSize (no verdict).
    """
    major_limit, minor_limit = limits_for(sample_size)
    counts = Counter(severities)
    unknown = set(counts) - set(SEVERITIES)
    if unknown:
        raise InvalidSeverity(f"Unknown severity: {sorted(unknown)}")

    if counts["critical"] >= 1:
        return "REJECT"
    if counts["major"] > major_limit:
        return "REJECT"
    if counts["minor"] > minor_limit:
        return "REJECT"
    return "ACCEPT"