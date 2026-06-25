import shutil
import tempfile
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from mysk.domain.import_url import ImportUrl
from mysk.domain.skill import Skill
from mysk.io import frontmatter
from mysk.io.github import DownloadError, download_skill
from mysk.io.skills import skill_library


def refresh_skill(
    name: Annotated[str, typer.Argument(help="Name of the skill to refresh.")],
) -> None:
    """Refresh an imported skill from its upstream source URL."""
    library = skill_library()
    skill_md_path = library / name / "SKILL.md"

    if not skill_md_path.exists():
        rprint(f"[red]Error:[/red] Skill {name!r} not found in the Skill Library.")
        raise typer.Exit(1)

    data, body = frontmatter.read(skill_md_path.read_text())
    try:
        skill = Skill.from_frontmatter(data)
    except (ValueError, KeyError) as exc:
        rprint(f"[red]Error:[/red] Malformed SKILL.md: {exc}")
        raise typer.Exit(1) from None

    if skill.mysk is None or not skill.mysk.provenance.is_imported:
        rprint(
            f"[red]Error:[/red] {name!r} is self-authored. "
            "Only imported skills (with a source URL) can be refreshed."
        )
        raise typer.Exit(1)

    if skill.mysk.provenance.modified:
        rprint(
            f"[red]Error:[/red] {name!r} has local changes (modified: true). "
            "Reset modified to false before refreshing."
        )
        raise typer.Exit(1)

    source = skill.mysk.provenance.source
    try:
        import_url = ImportUrl.parse(source)
    except ValueError as exc:
        rprint(f"[red]Error:[/red] Cannot parse source URL {source!r}: {exc}")
        raise typer.Exit(1) from None

    local_dir = library / name

    with tempfile.TemporaryDirectory() as tmp:
        tmp_skill_dir = Path(tmp) / name
        try:
            download_skill(import_url, tmp_skill_dir)
        except DownloadError as exc:
            rprint(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1) from None

        upstream_skill_md = tmp_skill_dir / "SKILL.md"
        if not upstream_skill_md.exists():
            rprint("[red]Error:[/red] Downloaded skill has no SKILL.md.")
            raise typer.Exit(1)

        upstream_data, upstream_body = frontmatter.read(upstream_skill_md.read_text())
        try:
            upstream_skill = Skill.from_frontmatter(upstream_data)
        except (ValueError, KeyError) as exc:
            rprint(f"[red]Error:[/red] Malformed upstream SKILL.md: {exc}")
            raise typer.Exit(1) from None

        refreshed = Skill(
            name=name,
            description=upstream_skill.description,
            mysk=skill.mysk,
        )
        new_skill_md = frontmatter.write(refreshed.to_frontmatter(), upstream_body)

        (tmp_skill_dir / "SKILL.md").write_text(new_skill_md)

        if _dirs_are_identical(local_dir, tmp_skill_dir):
            rprint(f"No changes — {name!r} is already up to date.")
            return

        shutil.rmtree(local_dir)
        shutil.copytree(tmp_skill_dir, local_dir)

    rprint(f"Refreshed {name!r}.")


def _dirs_are_identical(a: Path, b: Path) -> bool:
    a_files = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    b_files = {p.relative_to(b) for p in b.rglob("*") if p.is_file()}
    if a_files != b_files:
        return False
    return all((a / rel).read_bytes() == (b / rel).read_bytes() for rel in a_files)
