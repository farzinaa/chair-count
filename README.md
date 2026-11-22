# ASCII Floor Plan Chair Counter

A command-line solution to the apartment chair-counting exercise. It reads an
ASCII floor plan, counts the four chair types (W, P, S, C) for the apartment and
for each named room, and prints the legacy report with the room names in
alphabetical order.

## Run and test

From the project root:

```bash
python -m chair_counter rooms.txt
```

The report goes to stdout:

```text
total:
W: 14, P: 7, S: 3, C: 1
balcony:
W: 0, P: 2, S: 0, C: 0
...
```

`total` always comes first, the four types are always printed in W, P, S, C
order, and the rooms are sorted by name. Anything the tool wants to say about
the plan goes to stderr.

The test suite:

```bash
python -m unittest discover -s tests -v
```

## Algorithm

I treated the floor plan as a connectivity problem on a grid, rather than trying
to infer room shapes from their outlines.

Room names in parentheses are found with a regular expression. Their letters are
skipped when chairs are counted, and characters inside a name are never treated
as walls, so `(home-office)` is a name and not a room divider. Walls are `+`,
`-`, `|`, `/` and `\`; everything else is floor.

An iterative four-directional flood fill then walks each connected region,
picking up the chairs and the room name it finds on the way. A region with
exactly one name is that room.

Four neighbours is a deliberate choice. Diagonal contact is not a passage
between two rooms, and an eight-directional fill would slip through the diagonal
wall next to the bathroom in `rooms.txt` and merge it with the living room. The
traversal keeps its own stack, so a long plan cannot hit the recursion limit.

Short lines are padded rather than shortened, so a plan whose right-hand wall was
cut off turns into a room that is not closed, instead of one that quietly loses
a wall and swallows its neighbour.

## Plans that are not perfect

The numbers are the point, so the tool does not throw the report away over a
detail it cannot resolve. It reports what it can and explains the rest:

- **The apartment total is always complete.** It is counted independently of the
  rooms, so a chair in an unlabelled area, or in two rooms joined by an open
  doorway, still reaches `total:`. Only the per-room list is short in that case,
  and the warning says how many chairs were affected.
- A region with more than one name is not split by guessing.
- A room with a gap in its wall is counted, with a warning, because chairs from
  behind the gap may have been picked up.
- Text in parentheses outside the walls, such as a title above the plan, is
  ignored.
- Two rooms with the same name are added together, because the report has one
  entry per name.
- A room called `total` would collide with the heading of the summary, so it is
  kept out of the room list. Its chairs still count in the total.

A missing or non-UTF-8 file is the only thing that stops the tool, and then it
prints no report at all: no half-written file for the old system to read.

## Complexity

For a plan H lines high and W columns wide:

- Time: O(H × W). Every cell is examined a bounded number of times.
- Space: O(H × W) for the grid, the visited state and the fill stack.

Counting chairs during the traversal avoids a second pass over the plan. The aim
was a simple, predictable implementation rather than complexity for its own sake.

## Development approach

My background is primarily in applied mathematics, quantitative modelling and
algorithm development, particularly in financial trading and machine learning.
I approached this exercise by looking at the structure of the problem first:
what makes two floor cells part of the same room, and where can that question be
answered without guessing.

I use AI-assisted development tools as part of my regular workflow, mainly for
reviewing an implementation, challenging assumptions, hunting edge cases and
widening test coverage. The algorithmic decisions and the final validation are my
responsibility.

The goal was not just working code, but behaviour that is understandable,
reproducible and pinned down by tests where it is easy to be subtly wrong:
concave rooms, narrow passageways, diagonal walls, chair letters inside room
names, and the exact output.

## Public reference

I also came across Alexander Wendt's public implementation, which uses the same
four-directional flood fill. That is a natural choice for this problem. Mine puts
the emphasis on a complete apartment total, on not failing on plans it cannot
fully resolve, and on counting chairs during the traversal. Flood fill itself is
not something I claim to have invented.
