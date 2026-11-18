"""CSV writing."""


def _format_field(value, delimiter):
    if delimiter in value:
        return '"' + value + '"'
    return value


def write(rows, delimiter=","):
    """Serialise rows (lists of strings) to CSV text. Each row ends with a newline."""
    if len(delimiter) != 1:
        raise ValueError("delimiter must be a single character")
    out = []
    for row in rows:
        out.append(delimiter.join(_format_field(v, delimiter) for v in row) + "\n")
    return "".join(out)
