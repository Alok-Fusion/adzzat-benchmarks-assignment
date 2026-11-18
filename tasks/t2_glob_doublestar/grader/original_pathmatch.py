"""PRISTINE COPY of the original pathmatch, used by the grader as the "nothing else may change" oracle.

pathmatch: match '/'-separated paths against glob patterns.

Syntax
  *        any run of characters except '/'
  ?        exactly one character except '/'
  [abc]    one character from the set (ranges like a-z allowed); never matches '/'
  [!abc]   one character not in the set; never matches '/'
  **       intended: zero or more whole directories (see issue #12)
Everything else matches itself. A pattern must match the whole path.
"""
import re
from functools import lru_cache

__all__ = ["match", "filter_paths"]


def _class(body):
    negate = body.startswith("!")
    if negate:
        body = body[1:]
    body = "".join("\\" + c if c in "\\^[]" else c for c in body)
    return "[^/" + body + "]" if negate else "(?!/)[" + body + "]"


@lru_cache(maxsize=512)
def _compile(pattern):
    out = []
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        i += 1
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "[":
            j = i
            if j < n and pattern[j] == "!":
                j += 1
            if j < n and pattern[j] == "]":
                j += 1
            while j < n and pattern[j] != "]":
                j += 1
            if j >= n:              # no closing bracket: literal '['
                out.append(re.escape(c))
            else:
                out.append(_class(pattern[i:j]))
                i = j + 1
        else:
            out.append(re.escape(c))
    return re.compile("".join(out) + r"\Z", re.DOTALL)


def match(pattern, path):
    """Return True if `path` matches glob `pattern` in full."""
    return _compile(pattern).match(path) is not None


def filter_paths(pattern, paths):
    """Return the paths that match `pattern`, keeping their order."""
    return [p for p in paths if match(pattern, p)]
