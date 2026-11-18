# Task 2: `**` globstar without breaking anything else

**Tests failure category C (collateral damage), and D too.** Adding `**` is easy. The tricky part is that **every pattern without a globstar must behave exactly as it does today**, including odd ones such as `a**b`, unclosed `[` and `[]a]`. In the failure study (django-11133), the agent made the target test pass and broke 19 others. This task gives the same trap a clean, objective grader. It also has a symptom-fix path, and the grader catches it: a hack that makes all three issue examples pass still fails.

| Part | Where |
|---|---|
| Task statement (exactly what the agent sees) | [`TASK.md`](TASK.md) |
| Environment | [`environment/`](environment): `pathmatch/__init__.py` (~70 lines), `tests/test_match.py` (7 tests, **all pass at the start**), `Dockerfile` |
| Hidden grader | [`grader/grade.py`](grader/grade.py), [`grader/runner.py`](grader/runner.py), [`grader/original_pathmatch.py`](grader/original_pathmatch.py) (frozen copy of the original code) |
| Reference solution | [`reference/pathmatch/__init__.py`](reference/pathmatch/__init__.py): splits the pattern on `/` **only if** it has a globstar segment, otherwise builds exactly the old regex |
| Cheats and near misses | [`cheats/`](cheats) (5) |

## Grader (objective, about 1 s)

| Group | What is checked | Oracle |
|---|---|---|
| `spec_examples` (30) | Hand-written cases for all three rules in TASK.md, including the issue's examples | Written by hand |
| `globstar_vs_spec_oracle` (600) | Random patterns **with** a globstar segment | `oracle_match()`: a slow segment-by-segment matcher written straight from the spec, with memoised recursion. It is obviously correct and shares no code with the reference. |
| `unchanged_vs_original` (600) | Random patterns **without** one. 30% contain `**` *inside* a segment. The answer must equal the original code's answer. | `original_pathmatch.py` |
| `filter_paths` (4) | The second public function | `oracle_match()` |
| `regression_visible_tests` | Original visible tests | |

70% of the paths are **built from the pattern**, so that true answers are common. My first version used only random paths, and the *broken starting code* still passed 579/600 of the globstar cases. The test barely separated good code from bad. With paths built from the pattern, the start state passes about 386/600. I am keeping this note because it is the kind of grader weakness that review should catch.

The isolation is the same as Task 1: only `pathmatch/*.py` is copied, the code runs in a separate `-I` process with a timeout, a fresh seed is drawn every run and printed, and the judging happens outside the sandbox.

## Validation (`python run_checks.py`)
- Start: visible tests **pass**, grader **FAIL** (spec 18/30).
- Reference: **PASS** on every seed.
- `c1` turns every `**` into `.*` → FAIL. `c2` symptom fix that passes all three issue examples → FAIL. `c3` hard-codes the examples → FAIL. `c4` gets the globstar right but lets `a**b` cross `/` → FAIL. `c5` tampers with the tests → FAIL.

## What this task does not measure
Performance. Many globstars on a deep path can make the regex backtrack heavily, and the only guard is the 60 s timeout. A production version of this task would add a stated time limit and a stress-test group.
