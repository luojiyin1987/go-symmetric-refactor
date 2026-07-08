#!/usr/bin/env python3
"""Lightweight symmetry checks for Go code.

The checks are heuristic by design. They are meant to surface review targets for
an agent or maintainer, not to block builds as a strict linter.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

METHOD_RE = re.compile(
    r"^func\s+\(\s*(?P<recv>[A-Za-z_][A-Za-z0-9_]*)\s+\*?(?P<rtype>[A-Za-z_][A-Za-z0-9_]*)\s*\)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\("
)
FUNC_RE = re.compile(r"^func\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
TYPE_RE = re.compile(r"^type\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b")

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

LIFECYCLE_ORDER = {
    "New": 0,
    "Init": 1,
    "Start": 2,
    "Run": 3,
    "Join": 4,
    "Update": 5,
    "UpdateSelf": 5,
    "Get": 6,
    "List": 6,
    "Members": 6,
    "Close": 8,
    "Stop": 8,
    "Shutdown": 8,
}


@dataclass(frozen=True)
class Method:
    path: Path
    line: int
    recv: str
    recv_type: str
    name: str

    @property
    def exported(self) -> bool:
        return self.name[:1].isupper()


@dataclass
class ScanResult:
    methods_by_type: dict[str, list[Method]] = field(default_factory=lambda: defaultdict(list))
    funcs: list[tuple[Path, int, str]] = field(default_factory=list)
    types: list[tuple[Path, int, str]] = field(default_factory=list)


def iter_go_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.go")):
        parts = set(path.parts)
        if parts & SKIP_DIRS:
            continue
        yield path


def scan(root: Path) -> ScanResult:
    result = ScanResult()
    for path in iter_go_files(root):
        for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if match := METHOD_RE.match(line):
                method = Method(
                    path=path,
                    line=line_no,
                    recv=match.group("recv"),
                    recv_type=match.group("rtype"),
                    name=match.group("name"),
                )
                result.methods_by_type[method.recv_type].append(method)
                continue
            if match := FUNC_RE.match(line):
                result.funcs.append((path, line_no, match.group("name")))
                continue
            if match := TYPE_RE.match(line):
                result.types.append((path, line_no, match.group("name")))
                continue
    return result


def expected_receiver_name(type_name: str) -> str:
    uppercase = "".join(ch for ch in type_name if ch.isupper())
    if len(uppercase) >= 2:
        return uppercase.lower()
    return type_name[:1].lower()


def method_rank(name: str) -> tuple[int, str]:
    if name in LIFECYCLE_ORDER:
        return (LIFECYCLE_ORDER[name], name)
    if name.startswith(("Get", "List", "Find", "Lookup")):
        return (6, name)
    if name.startswith(("Set", "Add", "Remove", "Delete", "Update")):
        return (5, name)
    if name[:1].isupper():
        return (7, name)
    return (9, name)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def check_receiver_consistency(root: Path, result: ScanResult) -> list[str]:
    findings: list[str] = []
    for recv_type, methods in sorted(result.methods_by_type.items()):
        names = Counter(method.recv for method in methods)
        if len(names) <= 1:
            continue
        common = names.most_common(1)[0][0]
        details = ", ".join(f"{name}={count}" for name, count in names.most_common())
        findings.append(
            f"Receiver drift for {recv_type}: {details}. Consider normalizing to `{common}` if local style agrees."
        )
    return findings


def check_exported_before_private(root: Path, result: ScanResult) -> list[str]:
    findings: list[str] = []
    for recv_type, methods in sorted(result.methods_by_type.items()):
        seen_private = False
        for method in methods:
            if not method.exported:
                seen_private = True
                continue
            if seen_private:
                findings.append(
                    f"Exported method after private helper for {recv_type}: {rel(method.path, root)}:{method.line} {method.name}"
                )
    return findings


def check_lifecycle_order(root: Path, result: ScanResult) -> list[str]:
    findings: list[str] = []
    for recv_type, methods in sorted(result.methods_by_type.items()):
        ranked = [(method_rank(method.name), method) for method in methods]
        previous_rank: tuple[int, str] | None = None
        previous_method: Method | None = None
        for rank, method in ranked:
            if previous_rank is not None and rank[0] < previous_rank[0]:
                findings.append(
                    "Possible method-order drift for "
                    f"{recv_type}: {rel(previous_method.path, root)}:{previous_method.line} {previous_method.name} "
                    f"appears before {rel(method.path, root)}:{method.line} {method.name}."
                )
                break
            previous_rank = rank
            previous_method = method
    return findings


def check_missing_lifecycle_pairs(root: Path, result: ScanResult) -> list[str]:
    findings: list[str] = []
    stop_like = {"Stop", "Close", "Shutdown"}
    for recv_type, methods in sorted(result.methods_by_type.items()):
        names = {method.name for method in methods}
        if {"Start", "Run"} & names and not (stop_like & names):
            findings.append(
                f"Lifecycle asymmetry for {recv_type}: has Start/Run-style method but no Stop/Close/Shutdown-style counterpart."
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run lightweight Go symmetry checks.")
    parser.add_argument("root", nargs="?", default=".", help="Repository or package root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        parser.error(f"root does not exist: {root}")

    result = scan(root)
    findings: list[str] = []
    findings.extend(check_receiver_consistency(root, result))
    findings.extend(check_exported_before_private(root, result))
    findings.extend(check_lifecycle_order(root, result))
    findings.extend(check_missing_lifecycle_pairs(root, result))

    if not findings:
        print("No obvious symmetry findings.")
        return 0

    print("Symmetry review hints:")
    for index, finding in enumerate(findings, 1):
        print(f"{index}. {finding}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
