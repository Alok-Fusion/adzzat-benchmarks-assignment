# Part 1: Failure study (8 failed coding-agent attempts)

## Source and how I picked the cases

- **Run studied:** the public SWE-bench Verified leaderboard run *mini-SWE-agent v1.0.0 + Qwen2.5-Coder-32B-Instruct*. That is an open-weight model with a bash-only scaffold, 1 attempt per task, and a reported score of 9.0% (45/500). Its trajectories, patches and test logs are public on S3. `fetch_evidence.py` downloads them again and recomputes every number below. Small per-case summaries are in `evidence/`.
- **How I chose the 8:** I took the 455 unresolved tasks and checked how many of 5 stronger models solved each one, using the same leaderboard and the same mini-SWE-agent scaffold family: Claude Sonnet 4.5, Claude Opus 4.5, GPT-5, Gemini 2.5 Pro and Qwen3-Coder-480B. I sampled from both ends. **"5/5 solved"** suggests the task itself is fine. **"0/5 solved"** is a reason to suspect the task. I then read each trajectory, the submitted patch and the failing tests by hand. *This is not a random sample, so the counts below are not frequencies.*

| # | Task | How it ended | What happened (from the log) | Strong models that solved it |
|---|---|---|---|---|
| 1 | `django-11141` | Submitted, **empty patch** | It grepped for `if hasattr(migrations, "__file__")`, a string that is not in the file. It read "no match" as proof that its `sed` had removed the check, and submitted nothing. | 0/5 |
| 2 | `django-10999` | Submitted, **empty patch** | Its `sed` regex was over-escaped, so the file did not change. It then `cat`-ed the unchanged file and submitted. The task is also suspect, see Category E. | 0/5 |
| 3 | `matplotlib-25479` | Submitted, **patch = a new `test_colormap.py` only** | It "fixed" the user's reproduction script, renaming the colormap so the two names matched, and not the library. The error went away, so it declared success. Its `sed` edits to `lib/` are not in the diff. | 0/5 |
| 4 | `django-13128` | **Step limit** (250 turns) | It never edited a file. `cd apps && ls -d */` ran 44 times and `cd django && ls -d */` 42 times. In this scaffold every command runs in a fresh shell, so `cd` never persists, and the model never adjusted to that. | 5/5 |
| 5 | `scikit-learn-25232` | **Step limit** (250 turns) | The same `sed -i '/def __init__(self, /a ...fill_value=None,'` ran 64 times, along with two other commands about 60 times each. Each run appends another line. The scaffold drops the patch when the limit is hit, so the submission is empty. | 5/5 |
| 6 | `django-11133` | Submitted | It "manually replaced" `django/http/response.py` with a version written from memory, a 42 KB diff. The target test **passed**, but **19 previously passing tests broke**. Docstrings and `items()` became a property, among other changes. | 5/5 |
| 7 | `django-10914` | **APIError**: patch = error text | It put `FILE_UPLOAD_PERMISSIONS = 0o644` on the `FileSystemStorage` class instead of the global settings default, which is what the test checks (`None != 420`). The run then died on an OpenRouter error, and **the error message itself was submitted as the patch**. | 5/5 |
| 8 | `django-11179` | **APIError**: patch = error text | It inserted `instance.pk = None` early, then spent about 55 turns trying to build a Django test project inside `tests/i18n/sampleproject`. The provider error ended the run, and again the error text was graded as the patch. | 5/5 |

## Failure categories

**A. Edit not verified, so the agent claims success it did not get** (cases 1, 2, 3). *Looks like a real capability gap.*
The agent runs a check that cannot fail, or reads a check's result backwards, and then submits. In all three the final diff is empty or untouched in `lib/`, while the last message says the fix is done. The model is not tying "I changed X" to evidence that X changed, such as `git diff`.

**B. No progress detection, so the agent loops until the step limit** (cases 4, 5, and most of 8). *Mostly a capability gap, made worse by the scaffold.*
The same command repeats 40 to 60 times with no new information. Part of the cause is the environment: in a bash-only scaffold `cd` does not persist, and a weaker model keeps trying to navigate anyway. Stronger models in the *same* scaffold solve 4 and 5, so the scaffold alone does not explain it.

**C. Collateral damage: rewriting instead of editing** (case 6). *Capability gap.*
The fix is right, but the agent rewrote the whole file from memory and broke 19 unrelated tests. Hidden pass-to-pass (regression) tests are the only reason this counts as a failure. A grader that checks only the target behaviour would have passed it.

**D. Fix in the wrong place: local workaround or symptom fix** (cases 3 and 7). *Capability gap.*
The agent changes the reproduction (3), or patches one class where the issue asks for a project-wide default (7), so the visible symptom goes away but the real defect stays.

**E. Task or harness defects: the failure is not the model's fault.**
- **E1. Infrastructure errors scored as model failures** (cases 7 and 8). In this run, **238 of the 497 submitted "patches" are the text of a `litellm.APIError`**, and none of them resolved. The score shown is 9.0% (45/500). With those 238 removed it is 17.2% (45/262). The true figure is somewhere in between, and I cannot pin it down. Long runs may be the ones most likely to hit an API error, and long runs are more often failures, so 17.2% is probably too high. **The lesson for any benchmark we build:** an infrastructure error must be reported as "no result" and retried. It must never be counted as a wrong answer.
- **E2. Hidden tests require behaviour the issue never asks for** (case 2, and probably case 3). In `django-10999` the issue gives an exact one-line regex fix. I ran that regex against the expected values in the failing test's assertions, and **it fails all 5 negative-duration cases** (`evidence/django-10999_issue_fix_check.json`). The test expects the sign to apply to the whole duration (`-15:30` → −930 s) and `-01:-01` to be rejected. The issue says neither. In `matplotlib-25479` the hidden `test_colormap_equals` also requires two colormaps with different `.name` values to compare *equal*. That equality change is not in the issue. Both tasks were solved by 0 of 5 strong models, which fits a defect but does not prove one.

## What I cannot conclude from 8 cases

- **No rates.** The sample is hand-picked from two ends of the difficulty range. I cannot say "verification failures are X% of errors" or rank the categories by size.
- **Model or scaffold?** All 8 are one model in one scaffold with one attempt each. Loops (B) could come largely from mini-SWE-agent's stateless shell. I would need the same model in a stateful scaffold, such as SWE-agent or OpenHands, to separate the two.
- **"0/5 strong models solved it" suggests a defect but does not prove one.** For `django-11141` I could not find a defect. The issue reads clearly, and the 0/5 may come from a second check in `loader.py`. I have not verified that, so I leave it in category A as the model's failure and flag it as open.
- **One run per task.** At temperature > 0 a single failure says little about whether the model *can* do the task. A pass@k over about 5 seeds would be the minimum.
- **I did not rerun the tests myself.** I relied on the leaderboard's own logs, `test_output.txt` and `report.json`. For E2 I re-derived the regex behaviour in plain Python, not inside Django's test suite. The gold patches were not reachable because the Hugging Face API was down during my session.
- **Category boundaries are fuzzy.** Case 3 is both A and D. Case 8 is both B and E1. I gave each case its main category and noted the second one.

## How this fed into the tasks

- Categories **A + D** (symptom fix, unverified claim) → **Task 1** (`tinycsv`). The visible bug is in the reader, but the requirement is a *round-trip property*, so the writer has to be fixed too. A symptom fix passes every visible test and still fails the grader.
- Category **C** (collateral damage) → **Task 2** (`pathmatch`). The new feature is easy. The hard part is that *every other pattern must behave exactly as before*. That is checked against a frozen copy of the original code on hundreds of random patterns.
- Category **E2** shaped *how the tasks are written*. Every behaviour the grader checks is stated in `TASK.md`, edge cases included, such as `[""]` → `""` and `a/**` not matching `a`. Category **E1** shaped the harness: `local_model_runs/run_local.py` records an infrastructure error as `infra_error`, never as a failed attempt.
