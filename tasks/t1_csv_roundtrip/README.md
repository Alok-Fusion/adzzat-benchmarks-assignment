# Task 1: `tinycsv` round trip

**Tests failure categories A + D** from the failure study: unverified success claims and symptom fixes. The issue shows a bug in the **reader**. The stated requirement, though, is a round-trip property plus compatibility with other RFC 4180 tools. Meeting it means also finding and fixing the **writer**, which never escapes `"` and never quotes `\r`/`\n`, and dealing with records that contain line breaks. The reader must stop splitting the text line by line. An agent that fixes only what the issue shows, and then checks only the example in the issue, will pass every visible test and still fail.

| Part | Where |
|---|---|
| Task statement (exactly what the agent sees) | [`TASK.md`](TASK.md) |
| Environment (the agent's `/workspace`) | [`environment/`](environment): package `tinycsv/` (3 files, ~45 lines), `tests/test_basic.py` (6 tests, **all pass at the start**), `Dockerfile` |
| Hidden grader | [`grader/grade.py`](grader/grade.py) + [`grader/runner.py`](grader/runner.py) + a clean copy of the visible tests |
| Reference solution | [`reference/tinycsv/`](reference/tinycsv): a reader that runs a state machine over the whole text, and a writer that quotes and escapes correctly |
| Cheats and near misses the grader must reject | [`cheats/`](cheats) (5) |

## Environment
Python 3.11, standard library only, no network. The agent works in `/workspace` with a shell. [`environment/Dockerfile`](environment/Dockerfile) builds it: `python:3.11-slim`, the repo copied in, a non-root user. The graders and the reference are **not** in the image.

## Grader (objective, about 2 s)
`python grader/grade.py --submission <workspace>` → `PASS`/`FAIL` plus a count for each group of checks. Exit code 0 means pass.

| Group | What is checked | Oracle |
|---|---|---|
| `rfc_read` (10) | Hand-written RFC 4180 cases: `""` escapes, line breaks inside quotes, CRLF, no final newline, a lone `""`, other delimiters, non-ASCII text | Expected values written by hand |
| `interop_read` (150) | Text written by **Python's `csv` module** (`QUOTE_MINIMAL` and `QUOTE_ALL`, CRLF) → `read` must return the original rows | `csv.writer` |
| `interop_write` (150) | `write(rows)` must parse back to `rows` with **Python's `csv` module** | `csv.reader(strict=True)` |
| `roundtrip` (150) | `read(write(rows, d), d) == rows` on random tables | The property itself |
| `regression_visible_tests` | The **original** visible tests, from the grader's own copy | |

Random tables use characters picked to hit the hard cases often (`,` `;` `\t` `|` `"` `\r` `\n` `\r\n` `é` `😀`) and 4 delimiters. **A new seed is drawn on every grading run**, and it is printed so a failure can be reproduced.

**Anti-cheat design** (more in [`../../LEAKAGE_AND_REVIEW.md`](../../LEAKAGE_AND_REVIEW.md)):
1. Only `tinycsv/*.py` is copied out of the submission. Edited tests, `conftest.py` and `sitecustomize.py` are ignored.
2. The submission's code runs in a **separate `python -I` process** with a timeout. That process only produces outputs. All judging happens in the grader process, so the submission cannot patch the comparison.
3. `import csv` / `_csv` is **blocked inside the sandbox**. The oracle cannot be imported to do the work, and that rule is stated in TASK.md.

## Validation (run `python run_checks.py` from the repo root)
- Start state: visible tests **pass**, grader **FAIL** (rfc_read 6/10, roundtrip 17/150).
- Reference: **PASS** on every seed tried.
- `c1` wraps the stdlib csv → FAIL (blocked). `c2` fixes the reader only → FAIL. `c3` near miss, forgets `[""]` → FAIL on about 35/150. `c4` guts the visible tests and adds a `sitecustomize` → FAIL. `c5` hard-codes the issue's example → FAIL.
- **Every cheat passes the visible tests.** That is the point: the visible tests are not the bar.

## How I would check difficulty with many runs
See [`../../DIFFICULTY.md`](../../DIFFICULTY.md). In short: pass@1 and pass@k over at least 5 seeds per model across 3 or more models of different strength, which groups fail, and a check that a few strong models solve it, so we know it is solvable and fair. My one-shot runs with free local models are in [`../../local_model_runs/`](../../local_model_runs).

## What this task does not measure
How the agent explores a large codebase. The repo is about 45 lines and the bug's location is obvious. The difficulty is in reasoning from the spec, not in finding the code.
