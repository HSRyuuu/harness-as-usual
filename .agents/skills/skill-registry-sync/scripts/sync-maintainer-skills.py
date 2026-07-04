#!/usr/bin/env python3
"""Sync one-sided maintainer skill changes between .agents and .claude."""

from __future__ import annotations

import argparse
import fnmatch
import shutil
import subprocess
from pathlib import Path


LEFT_ROOT = Path(".agents/skills")
RIGHT_ROOT = Path(".claude/skills")
IGNORED_NAMES = {".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"}
IGNORED_PATTERNS = ("*.pyc", "*.pyo")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def is_ignored(path: Path) -> bool:
    return any(part in IGNORED_NAMES for part in path.parts) or any(
        fnmatch.fnmatch(path.name, pattern) for pattern in IGNORED_PATTERNS
    )


def changed_source_files(root: Path) -> set[Path]:
    output = run_git(["status", "--porcelain", "--untracked-files=all", "--", str(root)])
    changed: set[Path] = set()

    for line in output.splitlines():
        if not line:
            continue

        raw_path = line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]

        path = Path(raw_path)
        if not path.is_relative_to(root) or is_ignored(path):
            continue
        changed.add(path.relative_to(root))

    return changed


def source_files(root: Path) -> set[Path]:
    files: set[Path] = set()
    if not root.exists():
        return files

    for path in root.rglob("*"):
        if path.is_file() and not is_ignored(path):
            files.add(path.relative_to(root))
    return files


def differing_source_files() -> set[Path]:
    differing: set[Path] = set()
    all_files = source_files(LEFT_ROOT) | source_files(RIGHT_ROOT)

    for rel_path in all_files:
        left_path = LEFT_ROOT / rel_path
        right_path = RIGHT_ROOT / rel_path
        if not left_path.exists() or not right_path.exists():
            differing.add(rel_path)
            continue
        if left_path.read_bytes() != right_path.read_bytes():
            differing.add(rel_path)

    return differing


def skill_names_for(paths: set[Path]) -> set[str]:
    return {path.parts[0] for path in paths if path.parts}


def remove_stale_source_files(target_root: Path, source_file_set: set[Path], skill_names: set[str]) -> None:
    for rel_path in source_files(target_root):
        if rel_path.parts and rel_path.parts[0] in skill_names and rel_path not in source_file_set:
            (target_root / rel_path).unlink()


def prune_empty_dirs(root: Path, skill_names: set[str]) -> None:
    for skill_name in skill_names:
        skill_root = root / skill_name
        if not skill_root.exists():
            continue
        for directory in sorted(
            (path for path in skill_root.rglob("*") if path.is_dir() and not is_ignored(path)),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass


def copy_source_files(source_root: Path, target_root: Path, rel_paths: set[Path]) -> None:
    for rel_path in sorted(rel_paths):
        source_path = source_root / rel_path
        target_path = target_root / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def sync_one_direction(source_root: Path, target_root: Path, changed: set[Path]) -> None:
    skill_names = skill_names_for(changed)
    source_file_set = {
        rel_path
        for rel_path in source_files(source_root)
        if rel_path.parts and rel_path.parts[0] in skill_names
    }

    remove_stale_source_files(target_root, source_file_set, skill_names)
    copy_source_files(source_root, target_root, source_file_set)
    prune_empty_dirs(target_root, skill_names)


def print_paths(label: str, paths: set[Path]) -> None:
    print(label)
    if not paths:
        print("  - none")
        return
    for path in sorted(paths):
        print(f"  - {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Detect one-sided maintainer skill changes and optionally copy them "
            "between .agents/skills and .claude/skills."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply one-sided sync. Without this flag, only report the detected direction.",
    )
    args = parser.parse_args()

    left_changed = changed_source_files(LEFT_ROOT)
    right_changed = changed_source_files(RIGHT_ROOT)
    source_diffs = differing_source_files()

    print_paths("Codex-facing changes (.agents/skills):", left_changed)
    print_paths("Claude-facing changes (.claude/skills):", right_changed)

    if left_changed and right_changed:
        if not source_diffs:
            print("\nBoth sides have matching source-file changes. No sync needed.")
            return 0
        print(
            "\nBoth sides changed differently. Merge the intended source by hand, then rerun this script."
        )
        return 2

    if not left_changed and not right_changed:
        print("\nNo source-file changes detected.")
        return 0

    if left_changed:
        print("\nDirection: .agents/skills -> .claude/skills")
        if args.apply:
            sync_one_direction(LEFT_ROOT, RIGHT_ROOT, left_changed)
            print("Applied one-sided sync.")
        else:
            print("Dry run only. Rerun with --apply to copy.")
        return 0

    print("\nDirection: .claude/skills -> .agents/skills")
    if args.apply:
        sync_one_direction(RIGHT_ROOT, LEFT_ROOT, right_changed)
        print("Applied one-sided sync.")
    else:
        print("Dry run only. Rerun with --apply to copy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
