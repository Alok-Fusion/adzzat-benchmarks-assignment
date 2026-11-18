"""CSV writing (reference solution)."""

_SPECIAL = ('"', "\r", "\n")


def _format_field(value, delimiter):
    if delimiter in value or any(c in value for c in _SPECIAL):
        return '"' + value.replace('"', '""') + '"'
    return value


def write(rows, delimiter=","):
    """Serialise rows (lists of strings) to CSV text. Each row ends with a newline."""
    if len(delimiter) != 1:
        raise ValueError("delimiter must be a single character")
    out = []
    for row in rows:
        if len(row) == 1 and row[0] == "":
            line = '""'   # otherwise it would be a blank line, which holds no record
        else:
            line = delimiter.join(_format_field(v, delimiter) for v in row)
        out.append(line + "\n")
    return "".join(out)
