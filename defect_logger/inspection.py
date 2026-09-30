"""An inspection: a batch, a sample size and the defects recorded so far."""
from collections import Counter

from .verdict import (
    SEVERITIES,
    InvalidSeverity,
    compute_verdict,
    limits_for,
    validate_sample_size,
)


class Inspection:
    def __init__(self, batch_id, sample_size, defects=None):
        if not isinstance(batch_id, str) or not batch_id.strip():
            raise ValueError("Batch ID must not be empty.")
        validate_sample_size(sample_size)
        self.batch_id = batch_id.strip()
        self.sample_size = sample_size
        self.defects = []
        # Re-validate on load so a hand-edited file cannot smuggle in bad data.
        for d in defects or []:
            self.add_defect(d["severity"], d["description"])

    def add_defect(self, severity, description):
        if not isinstance(severity, str) or severity.strip().lower() not in SEVERITIES:
            raise InvalidSeverity(
                f"Severity must be one of {', '.join(SEVERITIES)}, got {severity!r}."
            )
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Description must not be empty.")
        self.defects.append(
            {"severity": severity.strip().lower(), "description": description.strip()}
        )

    def counts(self):
        c = Counter(d["severity"] for d in self.defects)
        return {s: c[s] for s in SEVERITIES}

    def limits(self):
        return limits_for(self.sample_size)

    def verdict(self):
        """Recomputed from the defects recorded so far, every time."""
        return compute_verdict(self.sample_size, [d["severity"] for d in self.defects])

    def to_dict(self):
        return {
            "batch_id": self.batch_id,
            "sample_size": self.sample_size,
            "defects": list(self.defects),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["batch_id"], data["sample_size"], data["defects"])