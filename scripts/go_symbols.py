#!/usr/bin/env python3
"""Print a compact symbol map for Go packages.

This script is intentionally lightweight. It does not try to fully parse Go.
It scans common top-level declarations well enough to give an agent a stable
map before it proposes symmetry-oriented refactors.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

TYPE_RE = re.compile(r"^type\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b")
FUNC_RE = re.compile(r"^func\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
METHOD_RE = re.compile(
    r"^func\s+\(\s*(?P<recv>[A-Za-z_][A-Za-z0-9_]*)\s+\*?(?P<rtype>[A-Za-z_][A-Za-z0-9_]*)\s*\)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\("
)
PACKAGE_RE = re.compile(r"^package\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b")
IMPORT_SINGLE_RE = re.compile(r'^import\s+"(?P<path>[^"]+)"')
IMPORT_BLOCK_ITEM_RE = re.compile(r'^\s*(?:[A-Za-z_][A-Za-z0-9_\.]*\s+)?"(?P<path>[^"]+)"')

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "vendor",
    "node_modules",
    "dist",
    "build",
    "tmp",
}


@dataclass
class Method:
    line: int
    recv: str
    recv_type: str
    name: str


@dataclass
class GoFile:
    path: Path
    package: str | None = None
    imports: list[str] = field(default_factory=list)
    types: list[tuple[int, str]] = field(default_factory=list)
    funcs: list[tuple[int, str]] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)


def iter_go_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.go")):
        parts = set(path.parts)
        if parts & SKIP_DIRS:
            continue
        yield path


def parse_go_file(path: Path) -> GoFile:
    result = GoFile(path=path)
    in_import_block = False

    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        line = raw.strip()

        if not line or line.startswith("//"):
            continue

        if match := PACKAGE_RE.match(line):
            result.package = match.group("name")
            continue

        if line == "import (":
            in_import_block = True
            continue

        if in_import_block:
            if line == ")":
                in_import_block = False
                continue
            if match := IMPORT_BLOCK_ITEM_RE.match(line):
                result.imports.append(match.group("path"))
            continue

        if match := IMPORT_SINGLE_RE.match(line):
            result.imports.append(match.group("path"))
            continue

        if match := TYPE_RE.match(line):
            result.types.append((line_no, match.group("name")))
            continue

        if match := METHOD_RE.match(line):
            result.methods.append(
                Method(
                    line=line_no,
                    recv=match.group("recv"),
                    recv_type=match.group("rtype"),
                    name=match.group("name"),
                )
            )
            continue

        if match := FUNC_RE.match(line):
            result.funcs.append((line_no, match.group("name")))
            continue

    return result


def print_file_symbols(file: GoFile, root: Path) -> None:
    rel = file.path.relative_to(root)
    print(f"\n# {rel}")
    if file.package:
        print(f"package {file.package}")

    if file.imports:
        print("imports:")
        for imp in file.imports:
            print(f"  - {imp}")

    if file.types:
        print("types:")
        for line, name in file.types:
            print(f"  {line}: type {name}")

    if file.funcs:
        print("funcs:")
        for line, name in file.funcs:
            print(f"  {line}: func {name}")

    if file.methods:
        print("methods:")
        for method in file.methods:
            print(f"  {method.line}: ({method.recv} *{method.recv_type}) {method.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact symbol map for Go files.")
    parser.add_argument("root", nargs="?", default=".", help="Repository or package root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        parser.error(f"root does not exist: {root}")

    files = list(iter_go_files(root))
    if not files:
        print("No Go files found.")
        return 0

    for path in files:
        print_file_symbols(parse_go_file(path), root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
