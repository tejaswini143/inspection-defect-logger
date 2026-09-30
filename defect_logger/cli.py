"""Command-line interface: start / add / list / verdict."""
import argparse
import re
import sys

from . import storage
from .inspection import Inspection
from .verdict import SEVERITIES, InvalidSampleSize

DEFAULT_FILE = "inspection.json"


def parse_sample_size(text):
    """Turn CLI text into an int, or raise InvalidSampleSize with a clear message."""
    if not re.fullmatch(r"-?\d+", text.strip()):
        raise InvalidSampleSize(f"Sample size must be a whole number, got {text!r}.")
    return int(text)


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--file", default=DEFAULT_FILE, help=f"inspection file (default: {DEFAULT_FILE})"
    )
    parser = argparse.ArgumentParser(
        prog="python -m defect_logger", description="Inspection Defect Logger"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("start", parents=[common], help="start an inspection")
    p.add_argument("--batch-id", required=True)
    p.add_argument("--sample-size", required=True, help="whole number, at least 1")
    p.add_argument("--force", action="store_true", help="replace an existing inspection")

    p = sub.add_parser("add", parents=[common], help="record a defect")
    p.add_argument("--severity", required=True, help="critical, major or minor")
    p.add_argument("--description", required=True)

    sub.add_parser("list", parents=[common], help="list recorded defects")
    sub.add_parser("verdict", parents=[common], help="show ACCEPT or REJECT")
    return parser


def _require(path):
    inspection = storage.load(path)
    if inspection is None:
        raise ValueError(
            f"No inspection started in {path}. Run: python -m defect_logger start "
            "--batch-id <id> --sample-size <n> (use the same --file for every command)"
        )
    return inspection


def _start(args, out):
    # Validate the input first, so bad input is always reported as bad input,
    # whether or not an inspection already exists.
    inspection = Inspection(args.batch_id, parse_sample_size(args.sample_size))
    if not args.force and storage.load(args.file) is not None:
        raise ValueError(
            f"An inspection already exists in {args.file}. Use --force to replace it."
        )
    storage.save(inspection, args.file)
    print(f"Started inspection {inspection.batch_id} (sample size {inspection.sample_size}).", file=out)


def _add(args, out):
    inspection = _require(args.file)
    inspection.add_defect(args.severity, args.description)
    storage.save(inspection, args.file)
    d = inspection.defects[-1]
    print(f"Recorded {d['severity']} defect: {d['description']}", file=out)


def _list(args, out):
    inspection = _require(args.file)
    if not inspection.defects:
        print("No defects recorded.", file=out)
    for i, d in enumerate(inspection.defects, 1):
        print(f"{i}. [{d['severity']}] {d['description']}", file=out)


def _verdict(args, out):
    inspection = _require(args.file)
    counts = inspection.counts()
    major_limit, minor_limit = inspection.limits()
    print(f"Batch: {inspection.batch_id} (sample size {inspection.sample_size})", file=out)
    print(
        f"Critical: {counts['critical']} (limit 0), "
        f"Major: {counts['major']} (limit {major_limit}), "
        f"Minor: {counts['minor']} (limit {minor_limit})",
        file=out,
    )
    print(f"Verdict: {inspection.verdict()}", file=out)


HANDLERS = {"start": _start, "add": _add, "list": _list, "verdict": _verdict}


def main(argv=None, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    try:
        HANDLERS[args.command](args, out)
    except (ValueError, storage.StorageError) as e:
        print(f"Error: {e}", file=err)
        return 1
    return 0