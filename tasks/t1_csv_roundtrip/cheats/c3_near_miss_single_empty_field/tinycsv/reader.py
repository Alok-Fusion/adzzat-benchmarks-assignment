"""CSV reading (reference solution).

A small state machine over the whole text, not line by line, so quoted
fields can hold line breaks.
"""


def read(text, delimiter=","):
    """Parse CSV text into a list of rows, each row a list of strings."""
    if len(delimiter) != 1:
        raise ValueError("delimiter must be a single character")

    rows = []
    row = []
    field = []
    in_quotes = False
    field_start = True      # nothing consumed yet for the current field
    record_started = False  # something consumed for the current record
    i, n = 0, len(text)

    def end_field():
        row.append("".join(field))
        field.clear()

    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':   # "" -> literal quote
                    field.append('"')
                    i += 2
                    continue
                in_quotes = False                      # closing quote
            else:
                field.append(ch)                       # delimiter, CR, LF are data here
            i += 1
            continue

        if ch == '"' and field_start:
            in_quotes = True
            field_start = False
            record_started = True
            i += 1
            continue
        if ch == delimiter:
            end_field()
            field_start = True
            record_started = True
            i += 1
            continue
        if ch == "\n" or (ch == "\r" and i + 1 < n and text[i + 1] == "\n"):
            if record_started:
                end_field()
                rows.append(row)
                row = []
            # a blank line outside quotes holds no record; skip it
            field_start = True
            record_started = False
            i += 2 if ch == "\r" else 1
            continue
        field.append(ch)
        field_start = False
        record_started = True
        i += 1

    if record_started:          # last record had no line ending
        end_field()
        rows.append(row)
    return rows
