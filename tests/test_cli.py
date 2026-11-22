"""Tests for the command line interface."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = (ROOT / "tests" / "fixtures" / "expected.txt").read_text()


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "chair_counter", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class CliTest(unittest.TestCase):
    def test_prints_the_report(self):
        result = run("rooms.txt")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, EXPECTED)
        self.assertEqual(result.stderr, "")

    def test_warnings_go_to_stderr_and_still_exit_zero(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write("+-----+\n|  W  |\n+-----+\n")
            path = handle.name
        try:
            result = run(path)
        finally:
            Path(path).unlink()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "total:\nW: 1, P: 0, S: 0, C: 0\n")
        self.assertIn("warning:", result.stderr)

    def test_missing_file(self):
        result = run("no-such-plan.txt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("error:", result.stderr)

    def test_directory_instead_of_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("error:", result.stderr)

    def test_file_that_is_not_utf8(self):
        with tempfile.NamedTemporaryFile("wb", suffix=".txt", delete=False) as handle:
            handle.write(b"\xff\xfe\x00junk")
            path = handle.name
        try:
            result = run(path)
        finally:
            Path(path).unlink()
        self.assertEqual(result.returncode, 1)
        self.assertIn("UTF-8", result.stderr)


if __name__ == "__main__":
    unittest.main()
