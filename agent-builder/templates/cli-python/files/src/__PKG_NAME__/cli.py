"""Command-line interface for __APP_TITLE__."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from __PKG_NAME__ import __version__, core


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="__APP_NAME__", description="__APP_DESCRIPTION__")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    hello = sub.add_parser("hello", help="print a greeting")
    hello.add_argument("name", nargs="?", default="world")
    hello.add_argument("--shout", action="store_true")
    hello.set_defaults(func=cmd_hello)

    scan = sub.add_parser("scan", help="summarise the files in a folder")
    scan.add_argument("folder", type=Path, nargs="?", default=Path("."))
    scan.add_argument("--no-recursive", action="store_true")
    scan.set_defaults(func=cmd_scan)
    return parser


def cmd_hello(args: argparse.Namespace) -> int:
    message = core.greet(args.name, args.shout)
    print(json.dumps({"message": message}) if args.json else message)
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    try:
        stats = core.scan(args.folder, recursive=not args.no_recursive)
    except NotADirectoryError:
        print(f"error: {args.folder} is not a folder", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(asdict(stats), indent=2))
        return 0
    print(f"{stats.files} files, {stats.total_bytes:,} bytes")
    for ext, count in stats.by_extension.items():
        print(f"  {ext:<12} {count}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
