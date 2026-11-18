# Task: tinycsv loses data on round trip

*This is the exact text the agent sees. The repository is in `/workspace` (the `environment/` folder here).*

---

**Issue #41: `read(write(rows))` does not give back `rows`**

We use `tinycsv` to save user notes and load them again later. Some notes come back changed:

```python
>>> import tinycsv
>>> rows = [["id", "note"], ["7", 'She said "ok", then left']]
>>> tinycsv.read(tinycsv.write(rows))
[['id', 'note'], ['7', 'She said ok, then left']]
```

Notes with line breaks in them get split into extra rows too.

**What we need.** Fix `tinycsv` so that both of these hold:

1. **Round trip.** For any `rows` that follows the rules below, `tinycsv.read(tinycsv.write(rows, d), d) == rows`, for any single-character `delimiter` `d` other than `"`, `\r` or `\n`.
2. **Works with other tools.** `read` must parse CSV written by other programs that follow RFC 4180, and other programs must be able to read what `write` produces. That means:
   - A field may be wrapped in double quotes. Inside a quoted field, `""` stands for one `"` character, and the delimiter, `\r` and `\n` are ordinary characters.
   - A record ends with `\n` or `\r\n`. One line ending after the last record does not start a new, empty record.
   - `write` must quote any field that contains the delimiter, `"`, `\r` or `\n`. It must also quote a row made of a single empty field (that row is written as `""`), so that it is not mistaken for a blank line. Other fields may be left unquoted.

**Rules for `rows`.** `rows` is a list of rows. Every row is a list of **one or more** `str` values. Values can contain any characters, including the delimiter, quotes, `\r`, `\n` and non-ASCII text.

**Constraints**
- Keep the public API the same: `read(text, delimiter=",")` and `write(rows, delimiter=",")`.
- **Do not use Python's `csv` module** (or `_csv`). `tinycsv` exists for runtimes that do not have it. Only the Python standard library is available. There is no network access.
- The existing tests in `tests/` must keep passing. Run them with `python -m unittest discover -s tests`.

When you are done, leave your changes in `/workspace`.
