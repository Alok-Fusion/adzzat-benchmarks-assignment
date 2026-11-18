# NEAR MISS: correct quoting, but forgets that a row [""] must be written as "" (else it is a blank line).
def _f(v, d):
    return '"' + v.replace('"', '""') + '"' if (d in v or any(c in v for c in '"\r\n')) else v
def write(rows, delimiter=","):
    return "".join(delimiter.join(_f(v, delimiter) for v in r) + "\n" for r in rows)
