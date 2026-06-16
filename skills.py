#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"


def default_skills_dir() -> Path:
    return Path.home() / ".claude" / "skills"


def _is_deprecated(skill: Path) -> bool:
    lines = (skill / "SKILL.md").read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("deprecated:") and "true" in line.lower():
            return True
    return False


def available_skills() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def list_skills(_: argparse.Namespace) -> int:
    for path in available_skills():
        suffix = "  [deprecated]" if _is_deprecated(path) else ""
        print(f"{path.name}{suffix}")
    return 0


def deploy_skills(args: argparse.Namespace) -> int:
    dest = args.dest.expanduser()
    dest.mkdir(parents=True, exist_ok=True)

    for skill in available_skills():
        if _is_deprecated(skill):
            print(f"Skipping deprecated skill: {skill.name}")
            continue

        target = dest / skill.name

        if target.exists() or target.is_symlink():
            if not target.is_symlink():
                print(f"Refusing to replace non-symlink: {target}", file=sys.stderr)
                return 1
            target.unlink()

        target.symlink_to(skill.resolve(), target_is_directory=True)
        print(f"Linked {skill.name} -> {target}")

    return 0


def cleanup_skills(args: argparse.Namespace) -> int:
    dest = args.dest.expanduser()
    if not dest.exists():
        print(f"Destination does not exist: {dest}", file=sys.stderr)
        return 1

    deprecated = {skill.name for skill in available_skills() if _is_deprecated(skill)}
    removed = 0

    for target in sorted(dest.iterdir()):
        if target.name not in deprecated:
            continue
        if not target.is_symlink():
            print(f"Refusing to remove non-symlink: {target}", file=sys.stderr)
            return 1
        target.unlink()
        print(f"Removed deprecated skill: {target.name}")
        removed += 1

    if removed == 0:
        print("No deprecated skills to clean up.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(func=list_skills)

    deploy_parser = subparsers.add_parser("deploy")
    deploy_parser.add_argument("--dest", type=Path, default=default_skills_dir())
    deploy_parser.set_defaults(func=deploy_skills)

    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("--dest", type=Path, default=default_skills_dir())
    cleanup_parser.set_defaults(func=cleanup_skills)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
