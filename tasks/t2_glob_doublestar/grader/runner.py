"""Runs INSIDE the sandbox subprocess. It only computes outputs and never judges them.

Usage: python -I runner.py <pkg_parent_dir> <cases.json> <out.json>
       python -I runner.py <pkg_parent_dir> --unittest <tests_dir>
"""
import json
import sys
import traceback


def main():
    sys.path.insert(0, sys.argv[1])
    if sys.argv[2] == "--unittest":
        import unittest
        suite = unittest.defaultTestLoader.discover(sys.argv[3], top_level_dir=sys.argv[3])
        result = unittest.TextTestRunner(verbosity=0, stream=sys.stderr).run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    cases = json.load(open(sys.argv[2], encoding="utf-8"))
    try:
        import pathmatch
    except Exception:
        err = "import failed: " + traceback.format_exc(limit=1)
        json.dump([{"error": err}] * len(cases), open(sys.argv[3], "w", encoding="utf-8"))
        return
    out = []
    for c in cases:
        try:
            if c["op"] == "match":
                res = pathmatch.match(c["pattern"], c["path"])
                res = res if isinstance(res, bool) else {"non_bool": repr(res)}
            else:
                res = list(pathmatch.filter_paths(c["pattern"], c["paths"]))
            out.append({"result": res})
        except Exception as e:
            out.append({"error": f"{type(e).__name__}: {e}"})
    json.dump(out, open(sys.argv[3], "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
