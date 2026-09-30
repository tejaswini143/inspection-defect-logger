# Decisions

## 1. Where the AI got it wrong

**The `start` command validated in the wrong order.** The AI's first version of
`start` checked whether an inspection file already existed *before* validating the
input. So with an inspection already on disk, running
`python -m defect_logger start --batch-id B-2 --sample-size 0` printed
"An inspection already exists ... Use --force" instead of the required clear
"Sample size must be at least 1" error (rule R4). I noticed it by running the CLI by
hand; all 64 automated tests were passing at that point, because none of them tried
invalid input while a file existed. The AI fixed it (input is validated first) and
added a regression test, `test_invalid_sample_size_is_reported_even_if_inspection_exists`,
which fails against the old ordering and passes now. In the AI session, look for the
message where I pasted my terminal output showing the wrong "already exists" error.

**A second, related bug found when I asked for more edge cases.** `start --force`
could not replace a corrupt inspection file: the code loaded the old file before
looking at `--force`, so a corrupt file raised an error even with `--force`, and the
only way out was to delete the file by hand. Fixed by checking `--force` first, with
the test `test_force_start_replaces_a_corrupt_file`.

Smaller AI mistakes in the same session: it gave a Unix-only
`source .venv/bin/activate` command when I was on Windows PowerShell, and its
"no inspection started" error did not say which file it had looked in, which
confused me when I mixed `--file` with the default file. Both were fixed (the README
has Windows and macOS/Linux commands; the error now names the file).

## 2. What I chose not to build, and why

Everything listed as out of scope (login, database, styling, deployment, multi-user,
editing or deleting defects). I also skipped a web UI (a CLI was explicitly fine),
managing several inspections at once beyond the `--file` option, and export or
reporting. I put the time into the verdict rule, input validation and tests instead.

## 3. What was ambiguous

- **Non-whole sample sizes** (`12.5`, `abc`): the brief only says "below 1 is
  invalid". I treat anything that is not a whole number as invalid too.
- **Starting when an inspection already exists:** the brief does not say. Overwriting
  would silently delete defects, which the brief says should not be deletable, so
  `start` refuses unless `--force` is given.
- **Defects vs sample size:** I allow more defects than units in the sample, since one
  unit can have several defects. The brief does not say either way.
- **Empty batch ID or description:** refused.
- **Severity casing:** `Major` is accepted and stored as `major`.
- **One inspection at a time:** "the inspection" in the brief reads as a single one.
- I checked the six required test cases against my reading of the rules; all six
  agree with the table, so I changed none of them.

## 4. Three things that could still go wrong that the tests do not cover

1. **Two commands writing at the same time.** Saving is atomic (no half-written
   file), but two processes doing load-then-save can overwrite each other's defect.
2. **Text starting with `-` and no spaces.** A description or batch ID such as
   `-scratch` is read by the argument parser as an option, and fails with a confusing
   "expected one argument" message (exit code 2). I reproduced this by hand. Writing
   `--description=-scratch` works, and `"-two words"` also works because of the
   space. I did not fix it because it is rare and has a workaround.
3. **Working directory and file location.** The default `inspection.json` is relative
   to the folder you run from, so running from another folder silently looks at a
   different file. Also, nothing limits the number of defects or the size of the file.

I also tested by hand on Windows that non-ASCII descriptions (`café ☃ 日本`) are saved
and listed correctly. The automated tests only use ASCII.