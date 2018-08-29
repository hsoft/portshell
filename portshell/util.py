from operator import itemgetter

def getcolumn(rows, index):
    return map(itemgetter(index), rows)

def tableize(rows):
    def toline(row):
        return ''.join(s.ljust(w + 1) for s, w in zip(row, widths))

    if not rows:
        return []
    columns = [getcolumn(rows, i) for i, _ in enumerate(rows[0])]
    widths = [max(len(s) for s in c) for c in columns]
    return map(toline, rows)
