# Part 3: Leakage, and feedback for a junior researcher

## 3a. Ways to pass my tasks without solving them

| # | How it could be gamed | Applies to | What stops it today | Still open |
|---|---|---|---|---|
| 1 | **Edit or delete the visible tests**, or add `conftest.py` / `sitecustomize.py` / `usercustomize.py` to change how the grader's Python behaves | both | The grader copies **only `<pkg>/*.py`** into a clean temp dir and runs its **own** copy of the visible tests. It uses `python -I`, so no user site-packages, no `PYTHON*` env vars and no cwd on the path. Cheats `t1/c4` and `t2/c5` show it. | none known |
| 2 | **Hard-code the examples in the issue** | both | The hidden checks are mostly **random cases from a fresh seed each run** (450 in t1, about 1,200 in t2), plus hand-written edge cases that are not in the issue. Cheats `t1/c5` and `t2/c3`. | A model that has memorised the hand-written cases could special-case them. Rotate them, see #7. |
| 3 | **Delegate to the oracle.** In t1, wrap Python's `csv` module, which is also what the grader uses to judge. | t1 | TASK.md bans it, and the sandbox **blocks the import** of `csv`/`_csv` with a meta-path hook. Cheat `t1/c1`. | Copying the C `_csv` algorithm into pure Python is allowed. It is a real solution. |
| 4 | **Patch the grader at runtime.** For example: monkeypatch `==`, swap `json`, read the expected answers from the grader's memory. | both | The submission runs in a **separate process** that only *produces outputs*. Expected values never enter that process, and the judging happens in the grader process. | A submission could write files or open sockets from its own process. The Docker image runs with `--network none` as a non-root user, and the grader dir is never mounted. |
| 5 | **Read the hidden grader or the reference** from disk | both | They are not in the agent's image (see the Dockerfile). The agent only ever sees `environment/`. | If someone runs the agent on this repo checkout, everything leaks. The harness must build the workspace from `environment/` only. |
| 6 | **Hang or crash so that a partial result passes** | both | A timeout on every sandbox call. A crash, timeout or missing output counts as a fail in every group, and `pass` needs every group at 100%. | none known |
| 7 | **The tasks are in the training data.** Once this repo is public, the reference and graders can be memorised. | both | Nothing today. | Before real use, keep a **private copy** with rotated surface details (names, delimiters, glob syntax). Track a canary string, and watch for "solves the private variant much worse than the public one". |
| 8 | **A grader that is too weak in places**, so a near-correct answer passes | t2 | I found and fixed one case: a test that used only random paths, where the broken code passed 579/600. Every cheat now fails at least one group. | Random testing can still miss rare edge cases. With more time I would **mutation-test the reference**: apply about 50 single-token mutants, and require the grader to reject at least 95% of the mutants that are not equivalent. |

### The one check I added and verified: run the submission in a sandbox and judge it elsewhere
`grader/runner.py` (in both tasks) runs the submission's code in a separate `python -I` process, with only the package files copied in, `csv` blocked in t1, and a timeout. It writes plain JSON outputs. `grader/grade.py` reads them in a different process that holds the oracles and does all the comparing. This one design blocks gaming routes 1, 3, 4 and 6 together. [`run_checks.py`](run_checks.py) proves it on every run: all 10 cheats and near misses **pass the visible tests and fail the grader**, while the reference passes on every seed.

### One thing these tasks do not measure
**Working in a realistic, large codebase.** Each repo is under 100 lines, the file to change is obvious, and the spec is complete and exact. So the tasks measure *careful reasoning from a spec, and not breaking things*. They do not measure *finding the right place in a large codebase*, *recovering from a vague or wrong issue*, or *agent persistence over many steps*. In the failure study those three explained most of the failures (categories B and E2). Nor do the tasks measure code quality, style or performance (t2 has no time limit). A passing solution can be ugly.

---

## 3b. Feedback for the junior researcher

> **Task under review:** "Write a function that sorts a list. The grader checks that the output contains the word 'sorted'."

Hi! Thanks for sending this early. That's the right time to get feedback. The core problem is that **the grader does not check the thing the task asks for**, so the score would carry no meaning. Here is what I'd change, in order of importance.

**1. The grader can be passed without sorting anything (blocking).** `print("sorted")` or `return "sorted"` passes, and a function that sorts correctly but prints nothing fails. So the task rewards the wrong behaviour and punishes the right one. A good test of any grader: *can you write a wrong solution that passes it, or a right one that fails it?* Here both are trivial. The grader should check *behaviour*: call the function on inputs and compare the result with `sorted(inputs)`, or check that it is in order *and* is a permutation of the input.

**2. The task statement is underspecified (blocking).** Before writing a grader, write down what "correct" means:
- **Interface:** function name and signature. Does it return a new list or sort in place?
- **Input domain:** ints only? floats, strings, mixed types? Duplicates? Empty list? `None`? Very large lists?
- **Order:** ascending? Stable for equal keys? Is a `key=` or `reverse=` argument needed?
- **Constraints:** is calling the built-in `sorted()` allowed? If not, say so *and enforce it* (block or detect it in a sandbox). Otherwise you are measuring whether the model knows `sorted()` exists, which every model does.

Anything the grader checks must appear in the statement, or the task is unfair (we see this "hidden requirement" defect in real SWE-bench tasks). Anything in the statement should be checked, or it is noise.

**3. Make the grader objective and hard to fool.** Use a fixed set of edge cases: `[]`, `[1]`, duplicates, already sorted, reverse sorted, negatives. Add random lists from a seed that changes every run and gets logged. Check stability with records that have equal keys, if you require it. Add a timeout, and run the candidate's code in a separate process so it cannot tamper with the checker.

**4. Ask what the task is for.** "Sort a list" is too easy for any current coding model, so it would score 100% for everyone and tell us nothing. If the goal is a benchmark task, start from a failure we have actually seen, for example "fixes the reported case and breaks a neighbour", and design the task so that failure shows up. Sorting could still work if there is a real twist: a custom collation, sorting a stream larger than memory, or fixing a subtly unstable sort in an existing codebase without breaking its other callers.

**5. Before you send the next version, validate it.** Include a reference solution that passes, and **at least two wrong solutions that must fail**: one that does nothing and one plausible near miss, such as unstable or descending. Run the grader on all of them. If a wrong solution passes, the grader isn't done. Then try it on a couple of models to see whether it is too easy.

The instinct to have an automatic grader is right, and so is keeping it small. Please send a revised statement, a grader, a reference, and the two wrong solutions, and we'll go through them together. Happy to pair on the grader if that helps.
