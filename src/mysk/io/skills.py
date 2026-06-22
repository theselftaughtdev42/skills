import os
from pathlib import Path

from platformdirs import user_data_dir
from pydantic import BaseModel, ConfigDict

from mysk.domain.skill import Skill
from mysk.io import frontmatter


def skill_library() -> Path:
    """Resolve the Skill Library directory, creating it if absent.

    Returns ``platformdirs.user_data_dir("mysk") / "skills"`` by default, or the
    ``MYSK_SKILLS_DIR`` path when that environment variable is set.
    """
    override = os.environ.get("MYSK_SKILLS_DIR")
    if override:
        library = Path(override).expanduser()
    else:
        library = Path(user_data_dir("mysk")) / "skills"
    library.mkdir(parents=True, exist_ok=True)
    return library


class SkillLoadResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    skill: Skill | None
    schema_error: str | None
    is_unmigrated: bool


def load_skills(skills_root: Path) -> list[SkillLoadResult]:
    """Load every skill under ``skills_root``, sorted alphabetically by name.

    Each result carries the parsed ``Skill`` when the frontmatter is valid, or a
    ``schema_error`` string when the block is present but malformed. Skills with
    no ``mysk`` block are returned with ``is_unmigrated=True``.
    """
    results = []
    for path in sorted(skills_root.glob("*/SKILL.md")):
        data, _ = frontmatter.read(path.read_text())
        try:
            skill = Skill.from_frontmatter(data)
        except (ValueError, KeyError) as exc:
            results.append(
                SkillLoadResult(
                    path=path,
                    skill=None,
                    schema_error=str(exc),
                    is_unmigrated=False,
                )
            )
            continue
        results.append(
            SkillLoadResult(
                path=path,
                skill=skill,
                schema_error=None,
                is_unmigrated=skill.mysk is None,
            )
        )
    return results
