"""Tests for the chair counter."""

import unittest
from pathlib import Path

from chair_counter import analyze, count_rooms

HERE = Path(__file__).resolve().parent
PLAN = (HERE.parent / "rooms.txt").read_text(encoding="utf-8-sig")
EXPECTED = (HERE / "fixtures" / "expected.txt").read_text()


def room(text, name):
    rooms, _, _ = count_rooms(text)
    return rooms[name]


class SamplePlanTest(unittest.TestCase):
    """rooms.txt is the plan the tool was written for."""

    def test_report_matches_expected_output(self):
        self.assertEqual(analyze(PLAN), EXPECTED)

    def test_plan_has_no_surprises(self):
        rooms, total, warnings = count_rooms(PLAN)
        self.assertEqual(warnings, [])
        self.assertEqual(
            total, {kind: sum(c[kind] for c in rooms.values()) for kind in "WPSC"}
        )
        self.assertEqual(
            sorted(rooms),
            [
                "balcony",
                "bathroom",
                "closet",
                "kitchen",
                "living room",
                "office",
                "sleeping room",
                "toilet",
            ],
        )

    def test_living_room_keeps_the_chair_from_the_hallway(self):
        # only reachable through the open passage around the bathroom
        self.assertEqual(
            room(PLAN, "living room"), {"W": 7, "P": 0, "S": 2, "C": 0}
        )

    def test_diagonal_wall_holds_the_bathroom_back(self):
        self.assertEqual(room(PLAN, "bathroom"), {"W": 0, "P": 1, "S": 0, "C": 0})
        self.assertEqual(room(PLAN, "kitchen"), {"W": 4, "P": 0, "S": 0, "C": 0})


class CountingTest(unittest.TestCase):
    def test_single_room(self):
        plan = "+--------+\n|(test)  |\n|W P S C |\n+--------+"
        self.assertEqual(
            analyze(plan),
            "total:\nW: 1, P: 1, S: 1, C: 1\n"
            "test:\nW: 1, P: 1, S: 1, C: 1\n",
        )

    def test_rooms_are_sorted_and_empty_rooms_printed(self):
        plan = "+-----+  +-----+\n|(b)  |  |(a)  |\n|P    |  |     |\n+-----+  +-----+"
        self.assertEqual(
            analyze(plan),
            "total:\nW: 0, P: 1, S: 0, C: 0\n"
            "a:\nW: 0, P: 0, S: 0, C: 0\n"
            "b:\nW: 0, P: 1, S: 0, C: 0\n",
        )

    def test_letters_inside_a_label_are_not_chairs(self):
        plan = "+---------+\n|(WORKSHOP)|\n|W  P  S  |\n+---------+"
        self.assertEqual(room(plan, "WORKSHOP"), {"W": 1, "P": 1, "S": 1, "C": 0})

    def test_diagonal_wall_keeps_rooms_apart(self):
        plan = "+-----+\n|(a) /|\n| W / |\n|  / W|\n| / W |\n|/(b) |\n+-----+"
        rooms, _, warnings = count_rooms(plan)
        self.assertEqual(warnings, [])
        self.assertEqual(rooms["a"], {"W": 1, "P": 0, "S": 0, "C": 0})
        self.assertEqual(rooms["b"], {"W": 2, "P": 0, "S": 0, "C": 0})

    def test_punctuation_in_a_name_is_not_a_wall(self):
        plan = "+--------------+\n|(home-office)W|\n+--------------+"
        self.assertEqual(
            room(plan, "home-office"), {"W": 1, "P": 0, "S": 0, "C": 0}
        )

    def test_chair_hanging_below_a_room_belongs_to_it(self):
        plan = (
            "+-----+-----+\n"
            "|(a)  |(b)  |\n"
            "|     |     |\n"
            "|     +-----+\n"
            "|  W  |\n"
            "+-----+"
        )
        self.assertEqual(room(plan, "a"), {"W": 1, "P": 0, "S": 0, "C": 0})
        self.assertEqual(room(plan, "b"), {"W": 0, "P": 0, "S": 0, "C": 0})


class WarningTest(unittest.TestCase):
    def test_chairs_without_a_room_still_count_in_the_total(self):
        rooms, total, warnings = count_rooms("+-----+\n|  W  |\n+-----+")
        self.assertEqual(rooms, {})
        self.assertEqual(total, {"W": 1, "P": 0, "S": 0, "C": 0})
        self.assertEqual(len(warnings), 1)
        self.assertIn("not in a room", warnings[0])

    def test_doorway_does_not_stop_the_report(self):
        plan = (
            "+-----+-----+\n"
            "|(a)  | (b) |\n"
            "|     |     |\n"
            "|           |\n"
            "|  W  |  P  |\n"
            "+-----+-----+"
        )
        rooms, total, warnings = count_rooms(plan)
        self.assertEqual(rooms, {})
        self.assertEqual(total, {"W": 1, "P": 1, "S": 0, "C": 0})
        self.assertIn("several rooms", warnings[0])
        self.assertEqual(analyze(plan), "total:\nW: 1, P: 1, S: 0, C: 0\n")

    def test_room_with_a_gap_is_still_counted(self):
        rooms, _, warnings = count_rooms("+-----+\n|(a)  |\n|  W  \n+-----+")
        self.assertEqual(rooms["a"], {"W": 1, "P": 0, "S": 0, "C": 0})
        self.assertIn("not closed", warnings[0])

    def test_text_outside_the_walls_is_ignored(self):
        plan = "(ground floor)\n+-----+\n|(a)  |\n|  W  |\n+-----+"
        rooms, total, warnings = count_rooms(plan)
        self.assertEqual(list(rooms), ["a"])
        self.assertEqual(total, {"W": 1, "P": 0, "S": 0, "C": 0})
        self.assertIn("outside the walls", warnings[0])

    def test_a_room_called_total_does_not_clash_with_the_heading(self):
        plan = (
            "+---------+  +-----+\n"
            "|(total)  |  |(a)  |\n"
            "|  W      |  |  P  |\n"
            "+---------+  +-----+"
        )
        report = analyze(plan)
        self.assertEqual(report.splitlines()[0], "total:")
        self.assertEqual(report.splitlines()[1], "W: 1, P: 1, S: 0, C: 0")
        self.assertEqual(report.count("total:"), 1)

    def test_duplicate_names_are_added_up(self):
        plan = "+-----+  +-----+\n|(a)  |  |(a)  |\n|  W  |  |  P  |\n+-----+  +-----+"
        rooms, _, warnings = count_rooms(plan)
        self.assertEqual(rooms["a"], {"W": 1, "P": 1, "S": 0, "C": 0})
        self.assertIn("more than once", warnings[0])


class RobustnessTest(unittest.TestCase):
    def test_windows_line_endings(self):
        plan = "+-----+\r\n|(a)  |\r\n|  W  |\r\n+-----+"
        self.assertEqual(room(plan, "a")["W"], 1)

    def test_empty_plan_gives_zero_totals(self):
        self.assertEqual(analyze(""), "total:\nW: 0, P: 0, S: 0, C: 0\n")

    def test_long_room_does_not_blow_the_stack(self):
        length = 5000
        plan = (
            "+" + "-" * length + "+\n"
            "|(room)" + " " * (length - 6) + "W|\n"
            "+" + "-" * length + "+"
        )
        self.assertEqual(room(plan, "room"), {"W": 1, "P": 0, "S": 0, "C": 0})

    def test_big_plan(self):
        size = 300
        rows = ["+" + "-" * size + "+", "|(big)" + " " * (size - 5) + "|"]
        expected = dict.fromkeys("WPSC", 0)
        for r in range(size):
            line = []
            for c in range(size):
                ch = "WPSC"[(r + c) % 4] if (r * 31 + c * 17) % 97 == 0 else " "
                if ch != " ":
                    expected[ch] += 1
                line.append(ch)
            rows.append("|" + "".join(line) + "|")
        rows.append("+" + "-" * size + "+")
        self.assertEqual(room("\n".join(rows), "big"), expected)


if __name__ == "__main__":
    unittest.main()
