 ### FILE: tinycsv/writer.py
```python
"""CSV writing."""


def _format_field(value, delimiter):
    if delimiter in value or '"' in value or '\r' in value or '\n' in value:
        return '"' + value.replace('"', '""') + '"'
    return value


def write(rows, delimiter=","):
    """Serialise rows (lists of strings) to CSV text. Each row ends with a newline."""
    if len(delimiter) != 1:
        raise ValueError("delimiter must be a single character")
    out = []
    for row in rows:
        formatted_row = [_format_field(v, delimiter) for v in row]
        out.append(delimiter.join(formatted_row) + "\n")
    return "".join(out)
```

### FILE: tinycsv/reader.py
```python
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
            fields.append("".join(field).replace('""', '"'))
            field = []
        else:
            field.append(ch)
    fields.append("".join(field).replace('""', '"'))
    return fields


def read(text, delimiter=","):
    """Parse CSV text into a list of rows, each row a list of strings."""
    if len(delimiter) != 1:
        raise ValueError("delimiter must be a single character")
    return [_parse_line(line, delimiter) for line in text.splitlines()]
```