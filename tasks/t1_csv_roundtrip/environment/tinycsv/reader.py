"""CSV reading."""


def _parse_line(line, delimiter):
    """Split one CSV record into its fields."""
    fields = []
    field = []
    in_quotes = False
    for ch in line:
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == delimiter and not in_quotes:
            fields.append("".join(field))
            field = []
        else:
            field.append(ch)
    fields.append("".join(field))
    return fields


def read(text, delimiter=","):
    """Parse CSV text into a list of rows, each row a list of strings."""
    if len(delimiter) != 1:
        raise ValueError("delimiter must be a single character")
    return [_parse_line(line, delimiter) for line in text.splitlines()]
