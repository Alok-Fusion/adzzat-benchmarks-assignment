# Task: `**` in pathmatch only matches exactly one directory

*This is the exact text the agent sees. The repository is in `/workspace` (the `environment/` folder here).*

---

**Issue #12: `**` should match any number of directories, including none**

Our CI config uses `pathmatch` to decide which test files to run:

```python
>>> from pathmatch import match
>>> match("src/**/test_*.py", "src/unit/test_a.py")
True
>>> match("src/**/test_*.py", "src/test_a.py")          # expected True
False
>>> match("src/**/test_*.py", "src/unit/db/test_b.py")  # expected True
False
```

**Required behaviour of `**`**

Split the pattern on `/` into segments. A segment that is **exactly** `**` is a *globstar*:

1. A globstar that is **not** the last segment matches **zero or more** whole path segments. So `a/**/b` matches `a/b`, `a/x/b` and `a/x/y/b`. `**/b` matches `b` and `x/y/b`.
2. A globstar that **is** the last segment matches **one or more** whole segments. So `a/**` matches everything inside `a` (`a/x`, `a/x/y`), but not `a` itself. A pattern that is only `**` matches any non-empty path.
3. Two stars that are **not** a whole segment, as in `a**b` or `x/**y`, keep their current meaning. They act exactly like a single `*` and never cross `/`.

**Constraint: nothing else may change.** Many config files already use this library. For every pattern that has no globstar segment, `match` must return exactly what it returns today, for every path. That includes `*`, `?`, `[...]`, `[!...]`, an unclosed `[`, and special characters.

Notes
- Paths use `/`, have no leading or trailing `/`, and have no empty segments. Patterns never contain `/` inside `[...]`.
- Keep the public API: `match(pattern, path)` and `filter_paths(pattern, paths)`.
- Only the Python standard library is available. There is no network access. Do not shell out to other programs.
- The existing tests must keep passing. Run them with `python -m unittest discover -s tests`.

When you are done, leave your changes in `/workspace`.
