from pathlib import Path

from typer.testing import CliRunner

from mysk.cli import app
from mysk.commands import deploy as deploy_cmd
from mysk.domain import LifecycleState, MyskBlock, Skill
from mysk.io.skills import SkillLoadResult
from mysk.io.targets import Target

runner = CliRunner()

_ACTIVE = Skill(
    name="tdd", description="d", mysk=MyskBlock(state=LifecycleState.ACTIVE)
)
_EXPERIMENTAL = Skill(
    name="run", description="d", mysk=MyskBlock(state=LifecycleState.EXPERIMENTAL)
)
_DEPRECATED = Skill(
    name="old", description="d", mysk=MyskBlock(state=LifecycleState.DEPRECATED)
)
_INIT = Skill(name="wip", description="d", mysk=MyskBlock(state=LifecycleState.INIT))

_CLAUDE = Target(name="claude", path=Path("/fake/.claude/skills"))


def _result(skill: Skill) -> SkillLoadResult:
    return SkillLoadResult(
        path=Path(f"/repo/skills/{skill.name}/SKILL.md"),
        skill=skill,
        schema_error=None,
        is_unmigrated=False,
    )


def _setup(
    monkeypatch,
    repo: Path | None = Path("/fake/repo"),
    targets: list[Target] | None = None,
    skills: list[Skill] | None = None,
    prompt_targets: list[Target] | None = None,
    prompt_skills: list[Skill] | None = None,
    reconcile_fn=None,
):
    monkeypatch.setattr(deploy_cmd, "find_source_repo", lambda: repo)
    monkeypatch.setattr(
        deploy_cmd,
        "discover_targets",
        lambda search_root=None: list(targets or []),
    )
    monkeypatch.setattr(
        deploy_cmd,
        "load_skills",
        lambda _: [_result(s) for s in (skills or [])],
    )
    monkeypatch.setattr(
        deploy_cmd,
        "_prompt_targets",
        lambda choices: list(prompt_targets or []),
    )
    monkeypatch.setattr(
        deploy_cmd,
        "_prompt_skills",
        lambda choices: list(prompt_skills or []),
    )
    if reconcile_fn is not None:
        monkeypatch.setattr(deploy_cmd, "reconcile_skill", reconcile_fn)


# --- flag validation ---


def test_skills_all_and_skills_flag_together_exits_with_error(monkeypatch):
    _setup(monkeypatch)

    result = runner.invoke(app, ["deploy", "--skills-all", "--skills", "tdd"])

    assert result.exit_code != 0
    assert "--skills-all" in result.output


# --- nothing selected ---


def test_nothing_selected_at_target_prompt_exits_cleanly(monkeypatch):
    _setup(
        monkeypatch,
        targets=[_CLAUDE],
        skills=[_ACTIVE],
        prompt_targets=[],
    )

    result = runner.invoke(app, ["deploy"])

    assert result.exit_code == 0
    assert "Nothing selected" in result.output


def test_nothing_selected_at_skill_prompt_exits_cleanly(monkeypatch):
    _setup(
        monkeypatch,
        targets=[_CLAUDE],
        skills=[_ACTIVE],
        prompt_targets=[_CLAUDE],
        prompt_skills=[],
    )

    result = runner.invoke(app, ["deploy"])

    assert result.exit_code == 0
    assert "Nothing selected" in result.output


# --- flag: --agents ---


def test_agents_flag_bypasses_target_prompt(monkeypatch, tmp_path):
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    source_skills = tmp_path / "repo" / "skills"
    (source_skills / "tdd").mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_ACTIVE],
    )

    result = runner.invoke(app, ["deploy", "--agents", "claude", "--skills-all"])

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills" / "tdd").is_symlink()


# --- flag: --skills ---


def test_skills_flag_bypasses_skill_prompt(monkeypatch, tmp_path):
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    source_skills = tmp_path / "repo" / "skills"
    (source_skills / "tdd").mkdir(parents=True)
    (source_skills / "run").mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_ACTIVE, _EXPERIMENTAL],
        prompt_targets=[claude],
    )

    result = runner.invoke(app, ["deploy", "--skills", "tdd"])

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills" / "tdd").is_symlink()
    assert not (tmp_path / ".claude" / "skills" / "run").exists()


# --- flag: --skills-all ---


def test_skills_all_deploys_every_skill_without_prompting(monkeypatch, tmp_path):
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    source_skills = tmp_path / "repo" / "skills"
    for name in ("tdd", "run", "old", "wip"):
        (source_skills / name).mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_ACTIVE, _EXPERIMENTAL, _DEPRECATED, _INIT],
        prompt_targets=[claude],
    )

    result = runner.invoke(app, ["deploy", "--skills-all"])

    assert result.exit_code == 0
    for name in ("tdd", "run", "old", "wip"):
        assert (tmp_path / ".claude" / "skills" / name).is_symlink()


# --- summary ---


def test_summary_shows_deployed_and_skipped_per_target(monkeypatch, tmp_path):
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    (tmp_path / ".claude" / "skills" / "old").mkdir()  # real dir → skipped

    source_skills = tmp_path / "repo" / "skills"
    (source_skills / "tdd").mkdir(parents=True)
    (source_skills / "old").mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_ACTIVE, _DEPRECATED],
        prompt_targets=[claude],
        prompt_skills=[_ACTIVE, _DEPRECATED],
    )

    result = runner.invoke(app, ["deploy"])

    assert result.exit_code == 0
    assert "tdd" in result.output
    assert "deployed" in result.output
    assert "old" in result.output
    assert "skipped" in result.output


def test_deprecated_skill_shows_warning_in_summary(monkeypatch, tmp_path):
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    source_skills = tmp_path / "repo" / "skills"
    (source_skills / "old").mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_DEPRECATED],
        prompt_targets=[claude],
        prompt_skills=[_DEPRECATED],
    )

    result = runner.invoke(app, ["deploy"])

    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()


# --- flag: --create-targets ---


def test_create_targets_creates_missing_skills_dir_when_agent_home_exists(
    monkeypatch, tmp_path
):
    (tmp_path / ".claude").mkdir()  # agent home exists, but skills/ doesn't
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")

    source_skills = tmp_path / "repo" / "skills"
    (source_skills / "tdd").mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_ACTIVE],
        prompt_targets=[claude],
        prompt_skills=[_ACTIVE],
    )

    result = runner.invoke(app, ["deploy", "--create-targets"])

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills").is_dir()
    assert (tmp_path / ".claude" / "skills" / "tdd").is_symlink()


def test_create_targets_skips_when_agent_home_missing(monkeypatch, tmp_path):
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")

    source_skills = tmp_path / "repo" / "skills"
    (source_skills / "tdd").mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_ACTIVE],
        prompt_targets=[claude],
        prompt_skills=[_ACTIVE],
    )

    result = runner.invoke(app, ["deploy", "--create-targets"])

    assert result.exit_code == 0
    assert not (tmp_path / ".claude" / "skills").exists()


# --- flag: --overwrite ---


def test_overwrite_replaces_non_symlink_dir(monkeypatch, tmp_path):
    claude = Target(name="claude", path=tmp_path / ".claude" / "skills")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    (tmp_path / ".claude" / "skills" / "tdd").mkdir()  # collision

    source_skills = tmp_path / "repo" / "skills"
    (source_skills / "tdd").mkdir(parents=True)

    _setup(
        monkeypatch,
        repo=tmp_path / "repo",
        targets=[claude],
        skills=[_ACTIVE],
        prompt_targets=[claude],
        prompt_skills=[_ACTIVE],
    )

    result = runner.invoke(app, ["deploy", "--overwrite"])

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills" / "tdd").is_symlink()
