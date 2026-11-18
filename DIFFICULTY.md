# Difficulty: what I measured, and how I would measure it with many runs

## What I actually ran (free local models, Ollama, GTX 1650 4 GB)

`local_model_runs/run_local.py`: **single-shot, not an agent**. Each model gets TASK.md plus every workspace file in one prompt and must reply with full replacement files. Its reply goes on top of a fresh workspace and the real hidden grader judges it (fixed seed 777). Raw replies are in `local_model_runs/raw/`, results in `local_model_runs/results_final.jsonl`.

| Model | Task | Attempts | Grader pass | Visible tests pass | What the replies did |
|---|---|---|---|---|---|
| qwen2.5:3b | t1 csv | 5 | **0/5** | 2/5 | Partial edits. 3/5 broke the existing tests. None fixed `""` escapes and multi-line records together. |
| qwen2.5:3b | t2 glob | 5 | **0/5** | 2/5 | 4/5 changed behaviour that had to stay the same (`unchanged_vs_original` 543–580/600), and 3/5 also broke the visible tests. That is category C, collateral damage, live. |
| deepseek-coder-v2 16B | t1 csv | 3 | **0/3** | 3/3 | All 3 fixed **only the writer's quoting** and left the line-by-line reader untouched (interop_write 131/150, roundtrip 8/150). It still missed the `[""]` rule. That is category D, a partial or symptom fix. |
| deepseek-coder-v2 16B | t2 glob | 3 | **0/3** | 3/3 | All 3 sent back the file **unchanged**, with scores identical to the start state. That is category A: nothing done, no check. |

**What these numbers can and cannot show.** They show that the tasks are not trivial for small open models, and that the grader picks up the same failure modes as the failure study. They **cannot** show how hard the tasks are for frontier agents. All of this is single-shot with small models, 16 attempts in total, and the 3 deepseek attempts per task were near-identical, so they are closer to 1 independent sample than 3. 0/16 is consistent with "too hard" *and* with "unfair". The only evidence that the tasks are solvable is the reference solution. I could not run a frontier agent for free, so I have not checked that a strong agent can solve them from TASK.md alone. That would be my first next step.

Harness note: my first grading pass scored one qwen attempt as a failure because **my grader crashed** printing non-ASCII text on a Windows cp1252 console. The same bug class appears in the SWE-bench run I studied (E1). I fixed the grader, added a separate `grader_error` status so a harness crash can never count as a model failure, and regraded everything from the saved replies.

## How I would check difficulty with many runs

1. **The panel.** At least 4 models spanning the range (small open, mid open, 2 frontier), all in **one agent scaffold** (for example mini-SWE-agent) and also one-shot. Use about **8 seeds per model per task** at the usual temperature. Report **pass@1 with a confidence interval** (Wilson, or bootstrap over seeds) and pass@8.
2. **Solvable and fair.** At least one frontier configuration should solve each task in at least 50% of runs. If none ever does, **review the task by hand before calling it hard**, because 0/N is what a broken task looks like too (lesson E2). Read every frontier failure's diff. If a reasonable solution failed a check the spec does not state, that is a task bug.
3. **Does it separate models?** A task that every model solves, or none does, carries no information. Good tasks have pass rates that rise with model strength. Across a set of tasks, check item discrimination: does the task correlate with each model's score on the rest of the set (point-biserial)? Drop or rework tasks near 0 or negative.
4. **Where they fail.** The grader reports group-level counts, so I would plot which groups each model fails. A "hard" task should fail for the reason it was designed for (t1: roundtrip/interop; t2: unchanged_vs_original). If failures cluster somewhere else, such as a timeout or import error, the difficulty is coming from the environment, not from the skill being tested.
5. **Stability.** Regrade each final workspace with 5 different grader seeds. A solution that passes on some seeds and fails on others is a near miss the grader only sometimes catches. Track how often that happens, and add a fixed regression case for each one found.
6. **Cost and steps.** Record turns, tokens and wall time per solve. Two tasks with the same pass rate but 10× different step counts are not equally hard.
