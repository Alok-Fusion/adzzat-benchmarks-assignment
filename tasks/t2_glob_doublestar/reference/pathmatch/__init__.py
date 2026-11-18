"""pathmatch: match '/'-separated paths against glob patterns (reference solution).

Syntax
  *        any run of characters except '/'
  ?        exactly one character except '/'
  [abc]    one character from the set (ranges like a-z allowed); never matches '/'
  [!abc]   one character not in the set; never matches '/'
  **       as a whole segment: zero or more whole segments (one or more when last)
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


def _translate(pattern):
    """Original translation, unchanged: glob text -> regex text (no anchors)."""
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
            if j >= n:
                out.append(re.escape(c))
            else:
                out.append(_class(pattern[i:j]))
                i = j + 1
        else:
            out.append(re.escape(c))
    return "".join(out)


@lru_cache(maxsize=512)
def _compile(pattern):
    segs = pattern.split("/")
    if "**" not in segs:
        # No globstar segment: build exactly the regex the old version built.
        return re.compile(_translate(pattern) + r"\Z", re.DOTALL)
    parts = []
    last = len(segs) - 1
    for k, seg in enumerate(segs):
        if seg == "**":
            # not last: zero or more "segment/" ; last: one or more segments
            parts.append(r"[^/]+(?:/[^/]+)*" if k == last else r"(?:[^/]+/)*")
        else:
            parts.append(_translate(seg) + ("" if k == last else "/"))
    return re.compile("".join(parts) + r"\Z", re.DOTALL)


def match(pattern, path):
    """Return True if `path` matches glob `pattern` in full."""
    return _compile(pattern).match(path) is not None


def filter_paths(pattern, paths):
    """Return the paths that match `pattern`, keeping their order."""
    return [p for p in paths if match(pattern, p)]
