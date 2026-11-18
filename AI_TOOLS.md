# AI tools used

| Tool | Used for |
|---|---|
| **Claude Code (Anthropic, Claude Opus 5.5)**, the coding agent in the Claude desktop app | It did most of the hands-on work: downloading and reading the public SWE-bench logs and trajectories; writing the evidence script; drafting both tasks, the graders, the reference solutions and the cheats; writing `run_checks.py` and the local-model harness; and drafting these write-ups. |
| **Ollama** running **qwen2.5:3b** and **deepseek-coder-v2 (16B)** locally (free) | These were the *models under test*, not helpers. They made single-shot attempts at both tasks to get a first difficulty signal (see DIFFICULTY.md). |

No paid APIs, models or cloud compute were used for this assignment.

**How I checked the AI's work.** Every number in the write-up comes from a script in this repo that can be rerun: `failure_study/fetch_evidence.py`, `run_checks.py` and `local_model_runs/run_local.py --regrade`. Validation caught several bugs: an oracle exception that crashed grader 1; a grader-2 test that could barely tell good code from bad (the broken code passed 579/600); and a Windows encoding crash in the grader that briefly counted a model attempt as a failure. All three are fixed and described in the docs.

I'm happy to walk through any part of this on the call and make changes live.
