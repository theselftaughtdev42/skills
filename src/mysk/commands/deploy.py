import sys
from typing import Annotated

import questionary
import typer
from rich import print as rprint

from mysk.domain.lifecycle import LifecycleState
from mysk.io.deploy import reconcile_skill
from mysk.io.skills import load_skills
from mysk.io.source_repo import find_source_repo
from mysk.io.targets import Target, discover_targets

_KNOWN_AGENTS: dict[str, str] = {
    "claude": ".claude",
    "cursor": ".cursor",
    "codex": ".agents",
}


def _prompt_targets(choices: list[questionary.Choice]) -> list[Target]:
    return (
        questionary.checkbox("Select Deployment Targets:", choices=choices).ask() or []
    )


def _prompt_skills(choices: list[questionary.Choice]) -> list[Target]:
    return questionary.checkbox("Select skills to deploy:", choices=choices).ask() or []


def deploy(
    agents: Annotated[
        str | None,
        typer.Option(
            "--agents", help="Comma-separated agent names, bypasses target prompt"
        ),
    ] = None,
    skills: Annotated[
        str | None,
        typer.Option(
            "--skills", help="Comma-separated skill names, bypasses skill prompt"
        ),
    ] = None,
    skills_all: Annotated[
        bool, typer.Option("--skills-all", help="Deploy all skills without prompting")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Replace non-symlink directories")
    ] = False,
    create_targets: Annotated[
        bool,
        typer.Option(
            "--create-targets",
            help="Create missing skills/ subdirectory when agent home exists",
        ),
    ] = False,
) -> None:
    """Deploy skills to Deployment Targets."""
    if skills_all and skills:
        rprint(
            "[red]--skills-all cannot be combined with --skills.[/red]", file=sys.stderr
        )
        raise typer.Exit(1)

    repo = find_source_repo()
    if repo is None:
        rprint("[red]Cannot find the mysk source repo.[/red]", file=sys.stderr)
        raise typer.Exit(1)

    results = load_skills(repo / "skills")
    all_skills = [r.skill for r in results if r.skill is not None]

    available_targets = discover_targets()

    # --- resolve targets ---
    if agents is not None:
        requested = {a.strip() for a in agents.split(",")}
        selected_targets = [t for t in available_targets if t.name in requested]
    else:
        choices = [questionary.Choice(t.label(), value=t) for t in available_targets]
        selected_targets = _prompt_targets(choices)

    if not selected_targets:
        rprint("Nothing selected.")
        return

    # --- resolve skills ---
    if skills_all:
        selected_skills = all_skills
    elif skills is not None:
        requested_skills = {s.strip() for s in skills.split(",")}
        selected_skills = [s for s in all_skills if s.name in requested_skills]
    else:
        choices = [
            questionary.Choice(f"{s.name} ({s.mysk.state.value})", value=s)
            for s in all_skills
        ]
        selected_skills = _prompt_skills(choices)

    if not selected_skills:
        rprint("Nothing selected.")
        return

    # --- deploy ---
    source_root = repo / "skills"

    for target in selected_targets:
        if not target.path.is_dir():
            if create_targets:
                agent_home = target.path.parent
                if agent_home.is_dir():
                    target.path.mkdir()
                else:
                    continue
            else:
                continue

        rprint(f"\n[bold]{target.label()}[/bold]")

        for skill in selected_skills:
            source_dir = source_root / skill.name
            outcome = reconcile_skill(source_dir, target.path, overwrite=overwrite)

            if skill.mysk and skill.mysk.state == LifecycleState.DEPRECATED:
                warn = "[yellow](deprecated — consider replacing)[/yellow]"
                rprint(f"  {skill.name:<20} {outcome}  {warn}")
            else:
                rprint(f"  {skill.name:<20} {outcome}")
