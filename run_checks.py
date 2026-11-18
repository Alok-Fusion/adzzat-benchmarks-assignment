"""Validate both tasks end to end.  Usage:  python run_checks.py [--seeds 3]

For each task this builds three kinds of workspace and grades each one:
  start      the untouched environment/              -> grader must say FAIL
  reference  environment/ + reference/ overlaid      -> must PASS on every seed
  cheats/*   environment/ + one cheat overlaid       -> must FAIL
It also runs each workspace's own visible tests, to show the gap between
"visible tests pass" and "hidden grader passes".
Needs only Python 3.9+ and the standard library.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS = ["t1_csv_roundtrip", "t2_glob_doublestar"]


def make_workspace(task_dir, overlay, tmp):
    ws = os.path.join(tmp, os.path.basename(overlay) if overlay else "start")
    shutil.copytree(os.path.join(task_dir, "environment"), ws)
    if overlay:
        shutil.copytree(overlay, ws, dirs_exist_ok=True)
    return ws


def visible_tests_pass(ws):
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                       cwd=ws, capture_output=True, text=True, timeout=60)
    return p.returncode == 0


def grade(task_dir, ws, seed):
    p = subprocess.run([sys.executable, os.path.join(task_dir, "grader", "grade.py"),
                        "--submission", ws, "--seed", str(seed)],
                       capture_output=True, text=True, timeout=300)
    first = p.stdout.splitlines()
    groups = [ln.split() for ln in first[1:] if ln.startswith("  ") and "/" in ln and not ln.strip().startswith("!")]
    summary = " ".join(f"{g[0]}={g[1]}" for g in groups)
    return p.returncode == 0, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    a = ap.parse_args()
    seeds = list(range(101, 101 + a.seeds))
    all_ok = True
    for t in TASKS:
        task_dir = os.path.join(ROOT, "tasks", t)
        print(f"\n=== {t}")
        print(f"{'workspace':36s} {'visible':8s} {'grader':8s} {'expected':9s} ok   detail (seed {seeds[0]})")
        runs = [("start", None, False), ("reference", os.path.join(task_dir, "reference"), True)]
        cdir = os.path.join(task_dir, "cheats")
        runs += [(f"cheat:{c}", os.path.join(cdir, c), False) for c in sorted(os.listdir(cdir))]
        with tempfile.TemporaryDirectory() as tmp:
            for name, overlay, should_pass in runs:
                ws = make_workspace(task_dir, overlay, tmp)
                vis = visible_tests_pass(ws)
                results = [grade(task_dir, ws, s) for s in (seeds if should_pass else seeds[:1])]
                passed = all(r[0] for r in results) if should_pass else results[0][0]
                ok = passed == should_pass
                all_ok &= ok
                print(f"{name:36s} {'pass' if vis else 'FAIL':8s} {'PASS' if passed else 'FAIL':8s} "
                      f"{'PASS' if should_pass else 'FAIL':9s} {'yes' if ok else 'NO!':4s} {results[0][1]}")
    print("\nALL CHECKS OK" if all_ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
