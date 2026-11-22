"""Chair counting for the ASCII floor plans of the old planning system."""

import re

CHAIR_TYPES = "WPSC"
WALLS = set("+-|/\\")
LABEL = re.compile(r"\(([^()]*)\)")
STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def analyze(text):
    """Return the report for a floor plan."""
    rooms, total, _ = count_rooms(text)
    return format_report(rooms, total)


def count_rooms(text):
    """Count the chairs of every room.

    Returns (rooms, total, warnings). rooms maps a room name to a dict such as
    {"W": 3, "P": 0, "S": 0, "C": 0}. total counts every chair in the plan,
    including the chairs that could not be tied to a room, so the number we
    hand to production is never short. warnings says what those chairs were.
    """
    lines = text.splitlines()
    if not lines:
        return {}, _empty(), []

    width = max(len(line) for line in lines)
    # Padded cells count as open floor, so a line that was cut off ends up as a
    # room that is not closed instead of one that quietly moves its wall inwards.
    lines = [line.ljust(width) for line in lines]

    labels, labelled_columns = _labels(lines)
    walk = []
    chairs = {}
    total = _empty()
    for row, line in enumerate(lines):
        labelled = labelled_columns.get(row, ())
        row_walk = []
        for col, ch in enumerate(line):
            # A room name is text, so a '-' or '/' inside one is not a wall.
            row_walk.append(ch not in WALLS or col in labelled)
            if ch in CHAIR_TYPES and col not in labelled:
                chairs[row, col] = ch
                total[ch] += 1
        walk.append(row_walk)

    rooms, warnings = {}, []
    seen = [[False] * width for _ in lines]

    for row in range(len(lines)):
        for col in range(width):
            if not walk[row][col] or seen[row][col]:
                continue
            names, counts, first, outside = _explore(
                (row, col), walk, seen, chairs, labels
            )
            found = sum(counts.values()) if counts else 0

            if not names:
                if found:
                    warnings.append(
                        f"{found} chair(s) at {_pos(first)} are not in a room, "
                        "only in the total"
                    )
                continue
            if len(names) > 1:
                warnings.append(
                    f"area at {_pos((row, col))} contains several rooms "
                    f"({', '.join(sorted(names))}), its {found} chair(s) are only "
                    "in the total"
                )
                continue

            name = names.pop()
            if outside and not found:
                warnings.append(f"label {name!r} is outside the walls")
                continue
            if outside:
                warnings.append(
                    f"room {name!r} is not closed, chairs behind the gap are "
                    "counted too"
                )
            if name.lower() == "total":
                warnings.append(
                    "a room is named 'total', it is kept out of the room list"
                )
            if ":" in name:
                warnings.append(
                    f"room name {name!r} contains ':', which may confuse the reader"
                )
            if name in rooms:
                warnings.append(
                    f"room {name!r} appears more than once, its counts are added"
                )
                if counts:
                    for kind in CHAIR_TYPES:
                        rooms[name][kind] += counts[kind]
            else:
                rooms[name] = dict(counts) if counts else _empty()

    return rooms, total, warnings


def format_report(rooms, total):
    """Render the counts the way the old system reads them."""
    lines = ["total:", _counts_line(total)]
    for name in sorted(rooms):
        if name.lower() == "total":
            # Would collide with the heading of the summary above.
            continue
        lines += [f"{name}:", _counts_line(rooms[name])]
    return "\n".join(lines) + "\n"


def _explore(start, walk, seen, chairs, labels):
    """Flood fill one open area and collect what is inside it.

    Returns the room names it contains, the chair counts, the first chair and
    whether the area runs into the edge of the drawing.
    """
    names, counts, first, outside = set(), None, None, False
    stack = [start]
    seen[start[0]][start[1]] = True
    while stack:
        row, col = stack.pop()
        if (row, col) in labels:
            names.add(labels[row, col])
        chair = chairs.get((row, col))
        if chair:
            if counts is None:
                counts, first = _empty(), (row, col)
            counts[chair] += 1
        # Four directions only: '/' and '\' are walls, and a diagonal step would
        # walk straight through them.
        for dr, dc in STEPS:
            r, c = row + dr, col + dc
            if not (0 <= r < len(walk) and 0 <= c < len(walk[0])):
                outside = True
            elif walk[r][c] and not seen[r][c]:
                seen[r][c] = True
                stack.append((r, c))
    return names, counts, first, outside


def _labels(lines):
    """Find the (name) labels.

    Returns the name per '(' position and, per row, the columns the labels take
    up, so the letters inside a label are not counted as chairs.
    """
    names = {}
    columns = {}
    for row, line in enumerate(lines):
        for match in LABEL.finditer(line):
            name = match.group(1).strip()
            if name:
                names[row, match.start()] = name
                columns.setdefault(row, set()).update(range(*match.span()))
    return names, columns


def _counts_line(counts):
    return ", ".join(f"{kind}: {counts[kind]}" for kind in CHAIR_TYPES)


def _empty():
    return dict.fromkeys(CHAIR_TYPES, 0)


def _pos(cell):
    row, col = cell
    return f"line {row + 1}, column {col + 1}"
