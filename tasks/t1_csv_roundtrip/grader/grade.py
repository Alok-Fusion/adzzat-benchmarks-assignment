"""Hidden grader for task t1_csv_roundtrip.

    python grade.py --submission <workspace dir> [--seed N] [--json]

Exit code 0 = PASS, 1 = FAIL. The agent never sees this folder.

How it judges:
  * Only the `tinycsv/*.py` files are copied out of the submission into a fresh
    temp dir. Edited tests, conftest.py, sitecustomize.py and so on have no effect.
  * The submission runs in a separate `python -I` process (runner.py) with
    `csv` blocked and a timeout. It only produces outputs.
  * This process judges those outputs. Python's own csv module is the oracle
    for compatibility with other tools.
  * Random cases use a fresh seed on every run (printed, so failures can be
    reproduced), so answers cannot be hard-coded.
"""
import argparse
import csv
import io
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT_S = 60
PKG = "tinycsv"

# Hand-written cases from RFC 4180 and the issue: (text, delimiter, expected rows)
FIXED_READ = [
    ('id,note\n7,"She said ""ok"", then left"\n', ",", [["id", "note"], ["7", 'She said "ok", then left']]),
    ('a,"line1\nline2",c\n', ",", [["a", "line1\nline2", "c"]]),
    ('a,b\r\nc,d\r\n', ",", [["a", "b"], ["c", "d"]]),
    ('a,b\nc,d', ",", [["a", "b"], ["c", "d"]]),                 # no final newline
    ('""\n', ",", [[""]]),                                       # single empty field
    ('"",""\n', ",", [["", ""]]),
    ('x;"a;b";"say ""hi"""\n', ";", [["x", "a;b", 'say "hi"']]),
    ('"crlf\r\ninside"\r\n', ",", [["crlf\r\ninside"]]),
    ('"日本,語","é"\n', ",", [["日本,語", "é"]]),
    ('a\t"b\tc"\n', "\t", [["a", "b\tc"]]),
]

# Characters chosen so the hard cases come up often.
ALPHABET = ["a", "b", "Z", "1", " ", ",", ";", "\t", "|", '"', '"', "\n", "\r", "\r\n", "é", "€", "😀"]
DELIMS = [",", ";", "\t", "|"]


def rand_rows(rng):
    rows = []
    for _ in range(rng.randint(1, 5)):
        ncols = rng.randint(1, 4)
        row = []
        for _ in range(ncols):
            k = rng.choice([0, 0, 1, 2, 3, 6])
            row.append("".join(rng.choice(ALPHABET) for _ in range(k)))
        rows.append(row)
    return rows


def oracle_write(rows, delim, quoting):
    buf = io.StringIO()
    csv.writer(buf, delimiter=delim, quotechar='"', lineterminator="\r\n", quoting=quoting).writerows(rows)
    return buf.getvalue()


def oracle_read(text, delim):
    return [r for r in csv.reader(io.StringIO(text, newline=""), delimiter=delim, quotechar='"', strict=True)]


def build_cases(seed, n_random=150):
    rng = random.Random(seed)
    cases, checks = [], []   # checks[i] = (group, description, judge(result) -> bool)

    for text, d, exp in FIXED_READ:
        cases.append({"op": "read", "text": text, "delim": d})
        checks.append(("rfc_read", f"read({text!r}, {d!r}) == {exp!r}", lambda r, exp=exp: r == exp))

    for _ in range(n_random):
        rows, d = rand_rows(rng), rng.choice(DELIMS)
        quoting = rng.choice([csv.QUOTE_MINIMAL, csv.QUOTE_ALL])
        text = oracle_write(rows, d, quoting)
        if oracle_read(text, d) != rows:   # skip anything the oracle itself cannot round-trip
            continue
        cases.append({"op": "read", "text": text, "delim": d})
        checks.append(("interop_read", f"read(csv-module output {text!r}, {d!r}) == {rows!r}",
                       lambda r, rows=rows: r == rows))

    for _ in range(n_random):
        rows, d = rand_rows(rng), rng.choice(DELIMS)
        cases.append({"op": "write", "rows": rows, "delim": d})
        def judge(out, rows=rows, d=d):
            return isinstance(out, str) and oracle_read(out, d) == rows
        checks.append(("interop_write", f"csv.reader(write({rows!r}, {d!r})) == rows", judge))
    return cases, checks


def run_sandbox(sub_pkg_parent, args):
    cmd = [sys.executable, "-I", os.path.join(HERE, "runner.py"), sub_pkg_parent] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)


def grade(submission, seed=None):
    seed = random.SystemRandom().randrange(2**31) if seed is None else seed
    report = {"task": "t1_csv_roundtrip", "seed": seed, "groups": {}, "first_failures": []}
    tmp = tempfile.mkdtemp(prefix="grade_t1_")
    try:
        # 1. copy only the package's .py files
        src = os.path.join(submission, PKG)
        dst = os.path.join(tmp, "pkg", PKG)
        os.makedirs(dst)
        if os.path.isdir(src):
            for f in os.listdir(src):
                if f.endswith(".py"):
                    shutil.copy(os.path.join(src, f), dst)
        pkg_parent = os.path.join(tmp, "pkg")

        # 2. hidden cases
        cases, checks = build_cases(seed)
        cpath, opath = os.path.join(tmp, "cases.json"), os.path.join(tmp, "out.json")
        json.dump(cases, open(cpath, "w", encoding="utf-8"))
        try:
            proc = run_sandbox(pkg_parent, [cpath, opath])
            outs = json.load(open(opath, encoding="utf-8")) if os.path.exists(opath) else None
            crash = None if outs is not None else (proc.stderr[-500:] or "no output")
        except subprocess.TimeoutExpired:
            outs, crash = None, f"timeout after {TIMEOUT_S}s"

        for i, (group, desc, judge) in enumerate(checks):
            g = report["groups"].setdefault(group, {"passed": 0, "total": 0})
            g["total"] += 1
            if outs is None:
                ok, got = False, crash
            else:
                o = outs[i]
                got = o.get("error") if "error" in o else o["result"]
                try:
                    ok = "error" not in o and judge(o["result"])
                except Exception as e:   # e.g. the oracle cannot even parse the output
                    ok, got = False, f"{got!r} -> oracle error {type(e).__name__}: {e}"
            if ok:
                g["passed"] += 1
            elif len(report["first_failures"]) < 5:
                report["first_failures"].append({"group": group, "expected": desc, "got": repr(got)[:300]})

        # 3. round trip uses both read and write in one call chain, so check it in a second sandbox pass
        rng = random.Random(seed + 1)
        rt_rows = [(rand_rows(rng), rng.choice(DELIMS)) for _ in range(150)]
        w_cases = [{"op": "write", "rows": r, "delim": d} for r, d in rt_rows]
        json.dump(w_cases, open(cpath, "w", encoding="utf-8"))
        g = report["groups"].setdefault("roundtrip", {"passed": 0, "total": len(rt_rows)})
        try:
            run_sandbox(pkg_parent, [cpath, opath])
            w_out = json.load(open(opath, encoding="utf-8"))
            r_cases = [{"op": "read", "text": o.get("result", ""), "delim": d}
                       for o, (_, d) in zip(w_out, rt_rows)]
            json.dump(r_cases, open(cpath, "w", encoding="utf-8"))
            run_sandbox(pkg_parent, [cpath, opath])
            r_out = json.load(open(opath, encoding="utf-8"))
            for (rows, d), wo, ro in zip(rt_rows, w_out, r_out):
                ok = "error" not in wo and "error" not in ro and ro["result"] == rows
                if ok:
                    g["passed"] += 1
                elif len(report["first_failures"]) < 5:
                    report["first_failures"].append({"group": "roundtrip",
                                                     "expected": f"read(write({rows!r}, {d!r})) == rows",
                                                     "got": repr(ro.get("result", ro.get("error")))[:300]})
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            report["first_failures"].append({"group": "roundtrip", "expected": "runs", "got": repr(e)})

        # 4. regression: the ORIGINAL visible tests (a clean copy kept here), not the workspace's copy
        tests_copy = os.path.join(tmp, "tests")
        shutil.copytree(os.path.join(HERE, "visible_tests"), tests_copy)
        try:
            p = run_sandbox(pkg_parent, ["--unittest", tests_copy])
            reg_ok = p.returncode == 0
            reg_detail = p.stderr[-400:]
        except subprocess.TimeoutExpired:
            reg_ok, reg_detail = False, "timeout"
        report["groups"]["regression_visible_tests"] = {"passed": int(reg_ok), "total": 1}
        if not reg_ok:
            report["first_failures"].append({"group": "regression_visible_tests", "expected": "all pass",
                                             "got": reg_detail})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    report["pass"] = all(g["passed"] == g["total"] and g["total"] > 0 for g in report["groups"].values())
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):   # Windows consoles default to cp1252; reports contain non-ASCII
        sys.stdout.reconfigure(encoding="utf-8")
    rep = grade(os.path.abspath(a.submission), a.seed)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(f"t1_csv_roundtrip  seed={rep['seed']}  {'PASS' if rep['pass'] else 'FAIL'}")
        for k, g in rep["groups"].items():
            print(f"  {k:26s} {g['passed']:4d}/{g['total']}")
        for f in rep["first_failures"][:3]:
            print(f"  ! [{f['group']}] expected {f['expected'][:160]}\n    got {f['got'][:160]}")
    sys.exit(0 if rep["pass"] else 1)


if __name__ == "__main__":
    main()
