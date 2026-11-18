import csv, io
def write(rows, delimiter=","):
    b = io.StringIO(); csv.writer(b, delimiter=delimiter, lineterminator="\n").writerows(rows); return b.getvalue()
