# Adzzat Labs take-home: Head of Research, Benchmarks

Two coding-benchmark tasks built from real coding-agent failures, with hidden graders, reference solutions, and validation that the graders reject cheats.

```bash
python run_checks.py          # validates both tasks end to end (Python 3.9+, stdlib only, ~1 min)
```
Expected last line: `ALL CHECKS OK`. A saved copy is in [`run_checks_output.txt`](run_checks_output.txt).

## Deliverables

| Asked for | Where |
|---|---|
| Failure categories and the examples behind them | [`failure_study/FAILURE_STUDY.md`](failure_study/FAILURE_STUDY.md), plus [`fetch_evidence.py`](failure_study/fetch_evidence.py), which re-downloads the public logs and recomputes every number |
| 2 tasks with graders and reference solutions in runnable form | [`tasks/t1_csv_roundtrip/`](tasks/t1_csv_roundtrip) and [`tasks/t2_glob_doublestar/`](tasks/t2_glob_doublestar). Each has `TASK.md`, `environment/` (with a Dockerfile), `grader/`, `reference/`, `cheats/`, `README.md` |
| How I would check difficulty | [`DIFFICULTY.md`](DIFFICULTY.md), including real single-shot runs with free local models ([`local_model_runs/`](local_model_runs)) |
| Leakage note, one check that guards against it, one thing not measured | [`LEAKAGE_AND_REVIEW.md` §3a](LEAKAGE_AND_REVIEW.md) |
| Feedback for the junior researcher | [`LEAKAGE_AND_REVIEW.md` §3b](LEAKAGE_AND_REVIEW.md#3b-feedback-for-a-junior-researcher) |
| AI tools used | [`AI_TOOLS.md`](AI_TOOLS.md) |
| Stretch: process for 100 tasks | [`PROCESS_100_TASKS.md`](PROCESS_100_TASKS.md) |

## Key findings in brief

1. **Failure study.** I studied 8 failed SWE-bench Verified attempts by an open model (Qwen2.5-Coder-32B in mini-SWE-agent). They fall into 5 categories: A, unverified "success"; B, loops until the step limit; C, collateral damage; D, a fix in the wrong place or a symptom fix; E, task or harness defects.
2. **A harness defect I quantified.** In that public run, **238 of 497 submitted "patches" are the text of an API error**. They were scored as model failures. The reported score is 9.0%. With those runs removed it is 17.2%, and the truth is somewhere in between.
3. **A task defect I verified.** In `django-10999` the one-line fix *the issue itself suggests* fails all 5 negative-duration cases in the hidden test. The test expects behaviour the issue never mentions.
4. **Task design.** Task 1 targets category D: the issue shows a reader bug, but the spec, a round-trip property, also needs the writer fixed. Task 2 targets category C: add `**` while 600 random patterns without a globstar must behave exactly as before. In both, **every cheat passes the visible tests and fails the hidden grader**.
5. **Local models: 0/16** single-shot. Their failures match the categories: writer-only fixes, unchanged files, broken regressions. Small sample, small models. See what that can and cannot show in DIFFICULTY.md.

## Grader design in one paragraph
Only the package's `.py` files are copied out of a submission. Edited tests, `conftest.py` and `sitecustomize.py` have no effect. The submission's code runs in a **separate `python -I` process** with a timeout, and in task 1 with `csv` blocked. That process only produces outputs. The **judging happens in another process** that holds the oracles: Python's `csv` module, a frozen copy of the original code, and a brute-force spec matcher. Random cases use a **fresh seed every run**, and the seed is printed so failures can be reproduced.

## Honest limits
- The Dockerfiles are written but **not built**: Docker Desktop was not running on my machine. All validation ran on the host with Python 3.11 on Windows.
- **No frontier-agent runs** (no paid APIs), so I have not shown that a strong agent can solve the tasks from TASK.md alone. Only the reference solution shows they are solvable. That is the first thing I would do next.
- The failure sample is hand-picked, one model, one attempt per task. It supports categories, not rates.

## What I would do next, in order
1. Run 2 frontier agents × 8 seeds on both tasks. Read every failure to rule out task defects.
2. Mutation-test both references, so the grader's strength gets a number.
3. Build and run the Docker images with `--network none`, and run the graders inside them.
4. Write the third task, on category B (progress and loop detection): a task with a misleading first lead, where the grader also records turns used.

## Portfolio evidence (prior benchmark work)
- **[orato_assessment](https://github.com/Alok-Fusion/orato_assessment)** (my own repo, self-made): an evaluation suite for Hindi and Hinglish speech models, covering ASR and TTS. It includes evaluation scripts, a test set of real WhatsApp voice notes with reference transcripts, and WER/CER scoring. One finding: whether a transcript is written in Devanagari or Latin script inflates WER on its own, so a fair metric has to normalise script first. That is the same kind of grader-validity problem as category E in this assignment.
- **This repository** is also self-made benchmark work: two tasks with hidden graders, oracles, and validation against cheats.

I have not yet worked on a large, team-built coding benchmark such as SWE-bench.

---
Repository layout
```
failure_study/   FAILURE_STUDY.md, fetch_evidence.py, evidence/ (per-case summaries)
tasks/t1_csv_roundtrip/    TASK.md  environment/  grader/  reference/  cheats/  README.md
tasks/t2_glob_doublestar/  TASK.md  environment/  grader/  reference/  cheats/  README.md
local_model_runs/          run_local.py, raw/ (model replies), results_final.jsonl
run_checks.py              start must FAIL · reference must PASS on 3 seeds · every cheat must FAIL
```
