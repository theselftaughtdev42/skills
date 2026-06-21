import sys
from pathlib import Path

import questionary
import typer
from rich import print as rprint

from mysk.io.deploy import reconcile_skill
from mysk.io.skills import load_skills
from mysk.io.source_repo import find_source_repo
from mysk.io.targets import discover_targets


def _ensure_target_dir(path: Path) -> str | None:
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
        try:
            display = "~/" + str(path.relative_to(Path.home()))
        except ValueError:
            display = str(path)
        return display
    return None


def deploy(
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace non-symlink directories at collision paths."
    ),
    agents: str | None = typer.Option(
        None,
        "--agents",
        help="Comma-separated agent names to target; skips the target prompt.",
    ),
    skills: str | None = typer.Option(
        None,
        "--skills",
        help="Comma-separated skill names to deploy; skips the skill prompt.",
    ),
    skills_all: bool = typer.Option(
        False,
        "--skills-all",
        help="Deploy every skill without prompting; skips the skill prompt.",
    ),
) -> None:
    """Deploy skills to selected Deployment Targets."""
    if skills_all and skills is not None:
        print("Cannot combine --skills-all with --skills.")
        raise typer.Exit(1)

    repo = find_source_repo()
    if repo is None:
        rprint("[red]Cannot find the mysk source repo.[/red]", file=sys.stderr)
        raise typer.Exit(1)

    targets = discover_targets()

    if agents is not None:
        names = {n.strip() for n in agents.split(",")}
        known = {t.name for t in targets}
        unknown = names - known
        if unknown:
            print(f"Unknown agent(s): {', '.join(sorted(unknown))}")
            raise typer.Exit(1)
        selected_targets = [t for t in targets if t.name in names]
    else:
        selected_targets = questionary.checkbox(
            "Select deployment targets:\n",
            choices=[questionary.Choice(t.label(), value=t) for t in targets],
        ).ask()

    if not selected_targets:
        print("Nothing selected.")
        raise typer.Exit(0)

    all_skills = load_skills(repo / "skills")
    deployable = [r for r in all_skills if r.skill and r.skill.mysk]

    if skills_all:
        selected_skills = deployable
    elif skills is not None:
        names = {n.strip() for n in skills.split(",")}
        known = {r.skill.name for r in deployable}
        unknown = names - known
        if unknown:
            print(f"Unknown skill(s): {', '.join(sorted(unknown))}")
            raise typer.Exit(1)
        selected_skills = [r for r in deployable if r.skill.name in names]
    else:
        selected_skills = questionary.checkbox(
            "Select skills to deploy:\n",
            choices=[
                questionary.Choice(
                    f"{r.skill.name} ({r.skill.mysk.state.value})", value=r
                )
                for r in deployable
            ],
        ).ask()

    if not selected_skills:
        print("Nothing selected.")
        raise typer.Exit(0)

    for target in selected_targets:
        print(f"\n{target.name}:")
        created = _ensure_target_dir(target.path)
        if created:
            print(f"  Created {created}")
        for skill_result in selected_skills:
            skill = skill_result.skill
            source_dir = skill_result.path.parent
            target_path = target.path / skill.name
            result = reconcile_skill(source_dir, target_path, overwrite=overwrite)
            line = f"  {skill.name}: {result.outcome}"
            if result.reason:
                line += f" ({result.reason})"
            print(line)
