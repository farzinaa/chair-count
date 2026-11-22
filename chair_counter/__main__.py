"""Command line entry point for the chair counter."""

import argparse
import sys
from pathlib import Path

from .core import count_rooms, format_report


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="chair_counter",
        description="Count chairs in an ASCII apartment floor plan.",
    )
    parser.add_argument("plan", type=Path, help="floor plan to read")
    args = parser.parse_args(argv)

    try:
        text = args.plan.read_text(encoding="utf-8-sig")
    except OSError as exc:
        print(f"error: cannot read {args.plan}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print(f"error: {args.plan} is not UTF-8 text", file=sys.stderr)
        return 1

    rooms, total, warnings = count_rooms(text)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    sys.stdout.write(format_report(rooms, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
