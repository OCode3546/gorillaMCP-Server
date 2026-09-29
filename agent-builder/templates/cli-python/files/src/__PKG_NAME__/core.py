"""Core logic for __APP_TITLE__. No argparse or printing here, so it's easy to test and reuse."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Stats:
    files: int
    total_bytes: int
    by_extension: dict[str, int]


def greet(name: str, shout: bool = False) -> str:
    message = f"Hello, {name}!"
    return message.upper() if shout else message


def scan(folder: Path, recursive: bool = True) -> Stats:
    """Count files and bytes per extension in a folder."""
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    pattern = "**/*" if recursive else "*"
    files = [p for p in folder.glob(pattern) if p.is_file()]
    by_ext = Counter(p.suffix.lower() or "(none)" for p in files)
    return Stats(
        files=len(files),
        total_bytes=sum(p.stat().st_size for p in files),
        by_extension=dict(by_ext.most_common()),
    )
