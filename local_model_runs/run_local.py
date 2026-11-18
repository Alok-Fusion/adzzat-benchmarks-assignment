"""Single-shot attempts on the two tasks with free local models served by Ollama.

    python local_model_runs/run_local.py --model qwen2.5:3b --samples 5

This is NOT an agent loop. The model gets TASK.md plus every file in the
workspace in one prompt, and has one chance to reply with full replacement
files. Its answer goes on top of a fresh copy of environment/ and is graded
by the real hidden grader (fixed seed 777, so models are compared on the same
cases). Raw replies are saved in local_model_runs/raw/ and one result line per
attempt is added to local_model_runs/results.jsonl.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "local_model_runs")
TASKS = {"t1_csv_roundtrip": "tinycsv", "t2_glob_doublestar": "pathmatch"}
SEED = 777

INSTRUCTIONS = """You are fixing a bug in a small Python repository. Read the task and the files below.
Reply with the COMPLETE new contents of every file you change, each in this exact format:

### FILE: <relative/path.py>
```python
<full file contents>
```

Only change files inside the package directory. Do not explain at length."""


def build_prompt(task):
    tdir = os.path.join(ROOT, "tasks", task)
    parts = [INSTRUCTIONS, "\n=== TASK ===\n", open(os.path.join(tdir, "TASK.md"), encoding="utf-8").read(),
             "\n=== REPOSITORY FILES ===\n"]
    env = os.path.join(tdir, "environment")
    for dp, _, fs in os.walk(env):
        for f in sorted(fs):
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(dp, f), env).replace("\\", "/")
                parts.append(f"### FILE: {rel}\n```python\n{open(os.path.join(dp, f), encoding='utf-8').read()}```\n")
    return "\n".join(parts)


def ollama(model, prompt, seed):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.7, "seed": seed, "num_predict": 3000, "num_ctx": 8192}})
    req = urllib.request.Request("http://localhost:11434/api/generate", body.encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.loads(r.read())


def parse_files(text, pkg):
    files = {}
    for m in re.finditer(r"###\s*FILE:\s*(\S+)\s*\n```(?:python)?\n(.*?)```", text, re.S):
        path = m.group(1).strip().lstrip("./")
        if path.startswith(pkg + "/") and path.endswith(".py") and ".." not in path:
            files[path] = m.group(2)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--tasks", nargs="*", default=list(TASKS))
    ap.add_argument("--regrade", action="store_true", help="grade saved raw replies again; no model calls")
    ap.add_argument("--results", default="results.jsonl")
    a = ap.parse_args()
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    for task in a.tasks:
        pkg = TASKS[task]
        prompt = build_prompt(task)
        for s in range(a.samples):
            t0 = time.time()
            tag = f"{task}__{a.model.replace(':', '_').replace('/', '_')}__s{s}"
            raw_path = os.path.join(OUT, "raw", tag + ".md")
            try:
                if a.regrade:   # re-grade a saved reply without calling the model again
                    text, resp = open(raw_path, encoding="utf-8").read(), {}
                else:
                    resp = ollama(a.model, prompt, seed=1000 + s)
                    text = resp.get("response", "")
            except Exception as e:  # report it; never count an infra error as a model failure
                rec = {"task": task, "model": a.model, "sample": s, "status": "infra_error", "detail": repr(e)[:300]}
                print(json.dumps(rec)); open(os.path.join(OUT, a.results), "a").write(json.dumps(rec) + "\n")
                continue
            secs = round(time.time() - t0)
            if not a.regrade:
                open(raw_path, "w", encoding="utf-8").write(text)
            files = parse_files(text, pkg)
            rec = {"task": task, "model": a.model, "sample": s, "secs": secs,
                   "files_changed": sorted(files), "eval_tokens": resp.get("eval_count")}
            if not files:
                rec.update(status="no_parsable_files", grader_pass=False)
            else:
                with tempfile.TemporaryDirectory() as tmp:
                    ws = os.path.join(tmp, "ws")
                    shutil.copytree(os.path.join(ROOT, "tasks", task, "environment"), ws)
                    for rel, body in files.items():
                        p = os.path.join(ws, rel)
                        os.makedirs(os.path.dirname(p), exist_ok=True)
                        open(p, "w", encoding="utf-8").write(body)
                    vis = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                                         cwd=ws, capture_output=True, text=True, timeout=120)
                    g = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "tasks", task, "grader", "grade.py"),
                                        "--submission", ws, "--seed", str(SEED), "--json"],
                                       capture_output=True, text=True, encoding="utf-8", timeout=600)
                    try:
                        rep = json.loads(g.stdout)
                    except json.JSONDecodeError:
                        # The grader itself crashed. That is a harness bug, not a model failure,
                        # so it gets its own status. (This happened once: a cp1252 print error.)
                        rec.update(status="grader_error", detail=g.stderr[-300:])
                        print(json.dumps(rec)[:300]); continue
                    rec.update(status="graded", visible_tests_pass=vis.returncode == 0, grader_pass=rep["pass"],
                               groups={k: f"{v['passed']}/{v['total']}" for k, v in rep["groups"].items()},
                               first_failure=(rep["first_failures"][:1] or [None])[0])
            print(json.dumps(rec, ensure_ascii=False)[:400], flush=True)
            open(os.path.join(OUT, a.results), "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
