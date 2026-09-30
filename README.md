# inspection-defect-logger

A small command-line tool for factory quality inspections. You start an inspection
with a batch ID and a sample size, record defects (critical, major or minor), list
them, and ask for a verdict. The verdict (ACCEPT or REJECT) is recomputed from the
recorded defects every time, using the acceptance-limits table from the brief. The
current inspection is stored in a JSON file (`inspection.json` by default).

Developed and tested on Python 3.14 (Windows). It uses only the standard library;
`pytest` is needed only to run the tests.

## Install

Windows (PowerShell):

```powershell
git clone <REPO-URL>
cd inspection-defect-logger
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell refuses to run the activate script, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first.

macOS / Linux:

```bash
git clone <REPO-URL>
cd inspection-defect-logger
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```
python -m defect_logger start --batch-id B-1 --sample-size 40
python -m defect_logger add --severity major --description "cracked lid"
python -m defect_logger list
python -m defect_logger verdict
```

Example output of `verdict`:

```
Batch: B-1 (sample size 40)
Critical: 0 (limit 0), Major: 1 (limit 3), Minor: 0 (limit 6)
Verdict: ACCEPT
```

Notes:

- Every command accepts `--file <path>` (default `inspection.json` in the current
  folder). Use the same `--file` for every command, or none of them.
- `start` refuses to overwrite an existing inspection unless you pass `--force`.
- A description or batch ID that starts with `-` and has no spaces (for example
  `-scratch`) is read as an option name. Write it with an equals sign instead:
  `--description=-scratch`.
- Errors are printed as `Error: ...` and the exit code is 1. An invalid sample size
  (below 1, or not a whole number) never produces a verdict.

## Run the tests

```
python -m pytest
```

## Verdict rule (from the brief)

Pick the table row with the largest "at least" value that is <= the sample size (no
interpolation). REJECT if there is at least 1 critical defect, or major defects are
greater than the major limit, or minor defects are greater than the minor limit.
Otherwise ACCEPT (including zero defects).

## Time spent

Roughly 4 hours.

See DECISIONS.md for where the AI went wrong, what I left out, and what is still risky.