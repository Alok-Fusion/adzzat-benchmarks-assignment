"""Runs INSIDE the sandbox subprocess. It only computes outputs and never judges them.

Usage: python -I runner.py <pkg_parent_dir> <cases.json> <out.json>
       python -I runner.py <pkg_parent_dir> --unittest <tests_dir>

The submission's code is imported here, in a separate process from the grader.
So the submission cannot patch the comparison logic, and it cannot reach the
oracle (Python's csv module, which the grader uses to judge).
"""
import importlib.abc
import json
import sys
import traceback

BLOCKED = {"csv", "_csv"}


class _Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BLOCKED:
            raise ImportError(f"import of '{name}' is not allowed in this task")
        return None


def _install_blocker():
    for name in list(sys.modules):
        if name.split(".")[0] in BLOCKED:
            del sys.modules[name]
    sys.meta_path.insert(0, _Blocker())


def main():
    pkg_parent = sys.argv[1]
    _install_blocker()
    sys.path.insert(0, pkg_parent)

    if sys.argv[2] == "--unittest":
        import unittest
        suite = unittest.defaultTestLoader.discover(sys.argv[3], top_level_dir=sys.argv[3])
        result = unittest.TextTestRunner(verbosity=0, stream=sys.stderr).run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    cases = json.load(open(sys.argv[2], encoding="utf-8"))
    out = []
    try:
        import tinycsv
    except Exception:
        err = "import failed: " + traceback.format_exc(limit=1)
        out = [{"error": err} for _ in cases]
        json.dump(out, open(sys.argv[3], "w", encoding="utf-8"))
        return
    for c in cases:
        try:
            if c["op"] == "read":
                res = tinycsv.read(c["text"], c["delim"])
                res = [list(r) for r in res]
            else:
                res = tinycsv.write(c["rows"], c["delim"])
            out.append({"result": res})
        except Exception as e:  # one bad case must not hide the others
            out.append({"error": f"{type(e).__name__}: {e}"})
    json.dump(out, open(sys.argv[3], "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
