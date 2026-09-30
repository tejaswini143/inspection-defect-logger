"""Save and load the current inspection as a JSON file."""
import json
import os
import tempfile

from .inspection import Inspection


class StorageError(Exception):
    """The inspection file could not be read or is not valid."""


def load(path):
    """Return the saved Inspection, or None if there is no file yet."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        raise StorageError(f"{path} is not valid JSON ({e}).") from e
    except OSError as e:
        raise StorageError(f"Could not read {path}: {e}.") from e
    try:
        return Inspection.from_dict(data)
    except (KeyError, TypeError, ValueError) as e:
        raise StorageError(f"{path} does not contain a valid inspection ({e!r}).") from e


def save(inspection, path):
    """Write atomically so a crash mid-write cannot leave a half-written file."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(inspection.to_dict(), f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise