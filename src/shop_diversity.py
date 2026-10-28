"""Finite heuristic resource coverage; never an equivalence/optimality proof."""
import math


def select_diverse(rows, limit, resource, cost):
    """Keep objective/strength anchors, then farthest normalized log resources.

    Return original objects. The expensive route VM is never copied or executed
    here; resource projections only choose which real branches to investigate.
    """
    if len(rows) <= limit:
        return list(rows)
    if limit < 1:
        raise ValueError('Positive selection limit required')
    values = [resource(row) for row in rows]
    quality = lambda r: .2 * math.log1p(r['hp']) + math.log1p(r['atk']) + math.log1p(r['def'])
    anchors = [min(range(len(rows)), key=lambda i: (cost(rows[i]), -quality(values[i]))),
               max(range(len(rows)), key=lambda i: quality(values[i]))]
    anchors += [max(range(len(rows)), key=lambda i: values[i][field])
                for field in ('atk', 'def', 'hp', 'experience')]
    raw = [[math.log1p(max(0, r[field])) for field in ('hp', 'atk', 'def', 'experience', 'money')]
           for r in values]
    lows = [min(v[j] for v in raw) for j in range(5)]
    spans = [max(v[j] for v in raw) - lows[j] for j in range(5)]
    points = [[(v[j] - lows[j]) / spans[j] if spans[j] else 0 for j in range(5)] for v in raw]
    chosen = []
    distances = [float('inf')] * len(rows)

    def add(i):
        chosen.append(i)
        for j, point in enumerate(points):
            distances[j] = min(distances[j], sum((a-b)**2 for a, b in zip(point, points[i])))
        for j in chosen:
            distances[j] = -1

    for i in anchors:
        if i not in chosen:
            add(i)
            if len(chosen) == limit:
                return [rows[i] for i in chosen]
    while len(chosen) < limit:
        add(max(range(len(rows)), key=lambda i: distances[i]))
    return [rows[i] for i in chosen]
