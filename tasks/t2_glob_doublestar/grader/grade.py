"""Hidden grader for task t2_glob_doublestar.

    python grade.py --submission <workspace dir> [--seed N] [--json]

Exit code 0 = PASS, 1 = FAIL. The agent never sees this folder.

Two oracles, both in this process:
  * original_pathmatch.py, a clean copy of the code before the fix. For any
    pattern with no globstar segment, the submission must agree with it exactly.
  * oracle_match() below, a slow but obviously correct segment-by-segment
    matcher written straight from the spec. Used for patterns that have a globstar.
The submission runs in a separate `python -I` process (runner.py) with a
timeout. Only pathmatch/*.py is copied in. Random cases use a fresh seed on
every run, and the seed is printed.
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import original_pathmatch as original  # noqa: E402

TIMEOUT_S = 60
PKG = "pathmatch"


def oracle_match(pattern, path):
    psegs = pattern.split("/")
    if "**" not in psegs:
        return original.match(pattern, path)
    segs = path.split("/")

    @lru_cache(maxsize=None)
    def m(i, j):
        if i == len(psegs):
            return j == len(segs)
        if psegs[i] == "**":
            if i == len(psegs) - 1:
                return len(segs) - j >= 1
            return any(m(i + 1, k) for k in range(j, len(segs) + 1))
        return j < len(segs) and original.match(psegs[i], segs[j]) and m(i + 1, j + 1)

    return m(0, 0)


# Spec examples, written by hand: (pattern, path, expected)
FIXED = [
    ("src/**/test_*.py", "src/test_a.py", True),
    ("src/**/test_*.py", "src/unit/test_a.py", True),
    ("src/**/test_*.py", "src/unit/db/test_b.py", True),
    ("src/**/test_*.py", "lib/unit/test_a.py", False),
    ("a/**/b", "a/b", True), ("a/**/b", "a/x/b", True), ("a/**/b", "a/x/y/b", True),
    ("a/**/b", "a/x/y/c", False), ("a/**/b", "ab", False),
    ("**/b", "b", True), ("**/b", "x/y/b", True), ("**/b", "xb", False),
    ("a/**", "a", False), ("a/**", "a/x", True), ("a/**", "a/x/y", True), ("a/**", "b/x", False),
    ("**", "x", True), ("**", "x/y/z", True),
    ("a/**/**/b", "a/b", True), ("**/**", "x", True),
    ("a**b", "axxb", True), ("a**b", "ax/xb", False),           # not a globstar: acts like *
    ("x/**y", "x/zzy", True), ("x/**y", "x/z/y", False),
    ("**.py", "app.py", True), ("**.py", "src/app.py", False),
    ("a/**/[bc]?.txt", "a/q/c1.txt", True), ("a/**/[!bc]?.txt", "a/q/c1.txt", False),
    ("docs/**/*.md", "docs/README.md", True), ("docs/**/*.md", "docs/a/b/c.md", True),
]

PATH_CH = ["a", "b", "c", ".", "_", "1", "[", "]", "!"]
SEG_TOK = ["a", "b", "c", ".", "_", "1", "*", "?", "[ab]", "[!a]", "[a-c]", "[]a]", "**", "!"]


def rand_path(rng):
    return "/".join("".join(rng.choice(PATH_CH) for _ in range(rng.randint(1, 3)))
                    for _ in range(rng.randint(1, 5)))


def rand_pattern(rng, globstar):
    if rng.random() < 0.6:   # mutate a real path so that matches come up often
        segs = rand_path(rng).split("/")
        out = []
        for s in segs:
            r = rng.random()
            if r < 0.15:
                out.append("*")
            elif r < 0.30:
                out.append("".join("?" if rng.random() < 0.4 else ch for ch in s))
            else:
                out.append(s)
    else:
        out = ["".join(rng.choice(SEG_TOK) for _ in range(rng.randint(1, 3))) for _ in range(rng.randint(1, 4))]
    # Never leave a bracket that is unclosed in one segment and closed in a later one,
    # because that would put '/' inside [...], which the spec rules out.
    out = [s.replace("[", "x") if s.count("[") > s.count("]") else s for s in out]
    if globstar:
        for _ in range(rng.randint(1, 2)):
            out.insert(rng.randint(0, len(out)), "**")
    else:
        out = [s if s != "**" else "*" for s in out]
        if rng.random() < 0.3:   # rule 3: '**' inside a segment (a**b) must still act like '*'
            k = rng.randrange(len(out))
            out[k] = rng.choice(["**" + out[k], out[k] + "**", out[k][:1] + "**" + out[k][1:]])
    p = "/".join(out)
    if not globstar and rng.random() < 0.1:
        p += "/x["          # unclosed bracket at the very end stays a literal
    return p


def instantiate(pattern, rng):
    """Make a path that probably matches `pattern` (the oracle decides the real answer)."""
    segs = []
    for s in pattern.split("/"):
        if s == "**":
            segs.extend(rand_path(rng).split("/")[: rng.randint(0, 3)])
            continue
        out, i = [], 0
        while i < len(s):
            c = s[i]
            if c == "*":
                out.append("".join(rng.choice("abc.") for _ in range(rng.randint(0, 2))))
            elif c == "?":
                out.append(rng.choice("abc1"))
            elif c == "[" and "]" in s[i + 2:]:
                j = s.index("]", i + 2)
                out.append(rng.choice("abcx"))
                i = j
            else:
                out.append(c)
            i += 1
        segs.append("".join(out) or "a")
    if segs and rng.random() < 0.15:   # sometimes nudge it so it should not match
        segs.insert(rng.randint(0, len(segs)), "zz")
    return "/".join(segs) or "a"


def build(seed, n=600):
    rng = random.Random(seed)
    cases, checks = [], []
    for pat, path, exp in FIXED:
        cases.append({"op": "match", "pattern": pat, "path": path})
        checks.append(("spec_examples", f"match({pat!r}, {path!r}) is {exp}", exp))
    for group, gs in (("globstar_vs_spec_oracle", True), ("unchanged_vs_original", False)):
        for _ in range(n):
            pat = rand_pattern(rng, gs)
            assert ("**" in pat.split("/")) == gs
            # 70% of paths are built from the pattern itself, so true answers are common;
            # the rest are random. A first version used only random paths, and the broken
            # starting code still passed 579/600 of those, so they told us almost nothing.
            r = rng.random()
            path = instantiate(pat, rng) if r < 0.7 else rand_path(rng)
            exp = oracle_match(pat, path)
            cases.append({"op": "match", "pattern": pat, "path": path})
            checks.append((group, f"match({pat!r}, {path!r}) is {exp}", exp))
    paths = ["src/a.py", "src/x/b.py", "README.md", "src/x/y/c.py", "lib/d.py"]
    for pat in ("src/**/*.py", "**/*.py", "*.md", "src/**"):
        exp = [p for p in paths if oracle_match(pat, p)]
        cases.append({"op": "filter", "pattern": pat, "paths": paths})
        checks.append(("filter_paths", f"filter_paths({pat!r}, ...) == {exp}", exp))
    return cases, checks


def run_sandbox(pkg_parent, args):
    cmd = [sys.executable, "-I", os.path.join(HERE, "runner.py"), pkg_parent] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)


def grade(submission, seed=None):
    seed = random.SystemRandom().randrange(2**31) if seed is None else seed
    report = {"task": "t2_glob_doublestar", "seed": seed, "groups": {}, "first_failures": []}
    tmp = tempfile.mkdtemp(prefix="grade_t2_")
    try:
        src, dst = os.path.join(submission, PKG), os.path.join(tmp, "pkg", PKG)
        os.makedirs(dst)
        if os.path.isdir(src):
            for f in os.listdir(src):
                if f.endswith(".py"):
                    shutil.copy(os.path.join(src, f), dst)
        pkg_parent = os.path.join(tmp, "pkg")

        cases, checks = build(seed)
        cpath, opath = os.path.join(tmp, "cases.json"), os.path.join(tmp, "out.json")
        json.dump(cases, open(cpath, "w", encoding="utf-8"))
        try:
            proc = run_sandbox(pkg_parent, [cpath, opath])
            outs = json.load(open(opath, encoding="utf-8")) if os.path.exists(opath) else None
            crash = None if outs is not None else (proc.stderr[-500:] or "no output")
        except subprocess.TimeoutExpired:
            outs, crash = None, f"timeout after {TIMEOUT_S}s"

        for i, (group, desc, exp) in enumerate(checks):
            g = report["groups"].setdefault(group, {"passed": 0, "total": 0})
            g["total"] += 1
            o = None if outs is None else outs[i]
            ok = o is not None and "error" not in o and o["result"] == exp
            if ok:
                g["passed"] += 1
            elif len(report["first_failures"]) < 5:
                got = crash if o is None else o.get("error", o.get("result"))
                report["first_failures"].append({"group": group, "expected": desc, "got": repr(got)[:300]})

        tests_copy = os.path.join(tmp, "tests")
        shutil.copytree(os.path.join(HERE, "visible_tests"), tests_copy)
        try:
            p = run_sandbox(pkg_parent, ["--unittest", tests_copy])
            reg_ok, detail = p.returncode == 0, p.stderr[-400:]
        except subprocess.TimeoutExpired:
            reg_ok, detail = False, "timeout"
        report["groups"]["regression_visible_tests"] = {"passed": int(reg_ok), "total": 1}
        if not reg_ok:
            report["first_failures"].append({"group": "regression_visible_tests", "expected": "all pass",
                                             "got": detail})
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
        print(f"t2_glob_doublestar  seed={rep['seed']}  {'PASS' if rep['pass'] else 'FAIL'}")
        for k, g in rep["groups"].items():
            print(f"  {k:26s} {g['passed']:4d}/{g['total']}")
        for f in rep["first_failures"][:3]:
            print(f"  ! [{f['group']}] expected {f['expected'][:160]}\n    got {f['got'][:160]}")
    sys.exit(0 if rep["pass"] else 1)


if __name__ == "__main__":
    main()
