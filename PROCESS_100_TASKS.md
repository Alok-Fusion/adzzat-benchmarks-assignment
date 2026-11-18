# Stretch: producing 100 tasks at steady quality (one page)

**Unit of work.** A *task package* in this repo's layout: `TASK.md`, `environment/` + Dockerfile, `grader/`, `reference/`, `cheats/` (at least 2: one empty or no-op, and one plausible near miss), and `META.yaml`. The metadata records the source failure (a log link), the category, what the task measures, what it does not measure, the author, the reviewer, and the date.

**Pipeline**
1. **Mine (weekly).** Researchers sample failed runs from public or own logs, tag each one with a category (as in FAILURE_STUDY.md), and log **E-type defects separately**, because those are harness bugs, not task ideas. Write task ideas only for categories with at least 3 real examples, so the tasks follow actual failures and not hunches.
2. **Author** (about 1 day per task) from a template. Rule: *every behaviour the grader checks is stated in TASK.md, and everything in TASK.md is checked.* Keep the repo small. Use an oracle that is independent of the reference (a frozen original, the stdlib, or a brute-force matcher).
3. **Automatic gate (CI, on every push).** `run_checks.py`-style. The start state must FAIL. The reference must PASS on 5 seeds. Every cheat must FAIL. Visible tests must pass at the start. Grading must be deterministic for a given seed. The Docker build must succeed with `--network none`. Grader runtime under 60 s. **Mutation test:** automatic mutants of the reference, at least 90% rejected.
4. **Human review** by a second researcher, with a checklist: Is the spec unambiguous (two reviewers write the expected output for 5 edge cases independently and must agree)? Is there any hidden requirement? Is there a leakage route not covered? Is it too close to a public repo or a known benchmark task (contamination)? Does it measure the category it claims? Reviewers do not review their own category every week, to avoid blind spots.
5. **Calibration run.** The model panel and seeds from DIFFICULTY.md. Accept the task if (a) at least one frontier configuration has pass@8 > 0, (b) it is not solved by everyone, and (c) a human has read every frontier failure and confirmed no task defect.
6. **Freeze and rotate.** Accepted tasks get a version and a canary string. Keep a private variant for held-out evaluation, and change surface details each quarter.

**Metrics on the dashboard (weekly)**
- Throughput: tasks accepted per researcher-week. Target about 4. For 100 tasks that is roughly 5 researchers for 5 weeks plus 1 reviewer-lead.
- **Quality:** % rejected at the auto gate and at human review, broken down by reason. *Post-release defect rate*, meaning tasks later found unfair or leaky, target under 3%. Every defect found adds a gate check.
- **Coverage:** tasks per failure category against the target mix. Languages and domains.
- **Signal:** pass-rate spread across the panel, item discrimination, and the share of tasks every model solves or none does (target under 10% of the set).
- **Reviewer agreement:** how often the second reviewer reverses the first. A rising rate means the template or the training needs work.
