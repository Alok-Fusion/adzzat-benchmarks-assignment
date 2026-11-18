# NEAR MISS (the failure seen in SWE-bench runs): fixes the reported symptom ("" inside quotes)
# in the line-based reader. The writer, embedded newlines and CRLF stay broken.
def _parse_line(line, delimiter):
    fields, field, in_q, i = [], [], False, 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_q and i + 1 < len(line) and line[i + 1] == '"':
                field.append('"'); i += 2; continue
            in_q = not in_q
        elif ch == delimiter and not in_q:
            fields.append("".join(field)); field = []
        else:
            field.append(ch)
        i += 1
    fields.append("".join(field))
    return fields
def read(text, delimiter=","):
    return [_parse_line(l, delimiter) for l in text.splitlines()]
