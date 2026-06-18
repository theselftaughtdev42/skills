import difflib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import questionary
import typer
from pydantic import BaseModel, ConfigDict, Field
from rich import print as rprint
from rich.markup import escape

from mysk.domain import LifecycleState
from mysk.io import frontmatter
from mysk.io.source_repo import find_source_repo

Select = Callable[[list[Path]], list[Path]]


class MigrationSummary(BaseModel):
    """Outcome of a migration run.

    ``upgraded`` are the skills that gained (or, under dry-run, would gain) a
    ``mysk`` block; ``already_compliant`` were owned beforehand; ``skipped`` are
    unmigrated skills the caller chose not to adopt. ``diffs`` holds the unified
    diff for each upgraded skill, so a dry-run can show exactly what would change.
    """

    model_config = ConfigDict(frozen=True)

    upgraded: list[Path] = Field(default_factory=list)
    already_compliant: list[Path] = Field(default_factory=list)
    skipped: list[Path] = Field(default_factory=list)
    diffs: dict[Path, str] = Field(default_factory=dict)


def migrate_skills(
    skills_root: Path, select: Select, *, dry_run: bool = False
) -> MigrationSummary:
    """Adopt unmigrated skills under ``skills_root`` into mysk management.

    A skill is unmigrated when its frontmatter has no ``mysk`` block. The
    caller's ``select`` chooses which unmigrated skills to adopt; each chosen
    one gains a ``mysk`` block at ``init`` while every other key and the body
    are left exactly as they were. ``dry_run`` computes the same result and
    diffs without touching any file.
    """
    compliant: list[Path] = []
    unmigrated: list[Path] = []
    for path in sorted(skills_root.glob("*/SKILL.md")):
        (unmigrated if _is_unmigrated(path) else compliant).append(path)

    chosen = set(select(unmigrated))
    upgraded: list[Path] = []
    skipped: list[Path] = []
    diffs: dict[Path, str] = {}
    for path in unmigrated:
        if path not in chosen:
            skipped.append(path)
            continue
        before = path.read_text()
        after = _with_init_block(before)
        upgraded.append(path)
        diffs[path] = _diff(path, before, after)
        if not dry_run:
            path.write_text(after)
    return MigrationSummary(
        upgraded=upgraded,
        already_compliant=compliant,
        skipped=skipped,
        diffs=diffs,
    )


def _with_init_block(text: str) -> str:
    data, body = frontmatter.read(text)
    data["mysk"] = {"state": LifecycleState.INIT.value}
    return frontmatter.write(data, body)


def _diff(path: Path, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        )
    )


def _print_diff(diff: str) -> None:
    for line in diff.splitlines(keepends=True):
        safe = escape(line)
        if line.startswith("+") and not line.startswith("+++"):
            rprint(f"[green]{safe}[/green]", end="")
        elif line.startswith("-") and not line.startswith("---"):
            rprint(f"[red]{safe}[/red]", end="")
        else:
            rprint(f"[dim]{safe}[/dim]", end="")


def _is_unmigrated(path: Path) -> bool:
    data, _ = frontmatter.read(path.read_text())
    return "mysk" not in data


def _prompt_for_skills(unmigrated: list[Path]) -> list[Path]:
    if not unmigrated:
        return []
    chosen = questionary.checkbox(
        "Select skills to migrate:\n",
        choices=[questionary.Choice(title=p.parent.name, value=p) for p in unmigrated],
    ).ask()
    return chosen or []


def _names(paths: list[Path]) -> str:
    return ", ".join(escape(p.parent.name) for p in paths)


def dev_migrate(
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would change without writing any files.",
        ),
    ] = False,
) -> None:
    """Adopt unmigrated skills into mysk by adding a `mysk` block at state init."""
    repo = find_source_repo()
    if repo is None:
        rprint(
            "[red]mysk dev migrate must be run from inside the mysk source repo.[/red]",
            file=sys.stderr,
        )
        raise typer.Exit(1)

    summary = migrate_skills(repo / "skills", _prompt_for_skills, dry_run=dry_run)

    if len(summary.upgraded) == 0 and len(summary.skipped) == 0:
        rprint("[bold]All skills are up-to-date. No migration necessary[/bold]")
        raise typer.Exit(0)

    if dry_run:
        rprint("[bold yellow]Dry run — no files will be modified[/bold yellow]")
        for path in summary.upgraded:
            rprint(f"\n[bold]{escape(path.parent.name)}[/bold]")
            _print_diff(summary.diffs[path])

    verb = "Would migrate" if dry_run else "Migrated"

    def _label(text: str, names: list[Path]) -> str:
        return text if not names else f"{text}: {_names(names)}."

    upgraded_label = _label(
        f"[green]{verb} {len(summary.upgraded)}[/green]",
        summary.upgraded,
    )
    skipped_label = _label(
        f"[yellow]Skipped {len(summary.skipped)}[/yellow]",
        summary.skipped,
    )

    rprint("\n[bold underline]Migration Summary[/bold underline]")
    rprint(f"  {upgraded_label}")
    rprint(f"  {skipped_label}")
