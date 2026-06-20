from pathlib import Path

from mysk.io.deploy import reconcile_skill


def _make_skill_dir(root: Path, name: str = "tdd") -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: tdd\ndescription: d\n---\n")
    return d


def test_fresh_deploy_creates_symlink_and_returns_deployed(tmp_path):
    source_dir = _make_skill_dir(tmp_path / "repo" / "skills")
    target_skills = tmp_path / ".claude" / "skills"
    target_skills.mkdir(parents=True)

    result = reconcile_skill(source_dir, target_skills)

    assert result == "deployed"
    link = target_skills / "tdd"
    assert link.is_symlink()
    assert link.resolve() == source_dir.resolve()


def test_non_symlink_collision_returns_skipped(tmp_path):
    source_dir = _make_skill_dir(tmp_path / "repo" / "skills")
    target_skills = tmp_path / ".claude" / "skills"
    target_skills.mkdir(parents=True)
    (target_skills / "tdd").mkdir()  # real directory, not a symlink

    result = reconcile_skill(source_dir, target_skills)

    assert result == "skipped"
    assert not (target_skills / "tdd").is_symlink()


def test_overwrite_replaces_non_symlink_dir_and_returns_deployed(tmp_path):
    source_dir = _make_skill_dir(tmp_path / "repo" / "skills")
    target_skills = tmp_path / ".claude" / "skills"
    target_skills.mkdir(parents=True)
    (target_skills / "tdd").mkdir()

    result = reconcile_skill(source_dir, target_skills, overwrite=True)

    assert result == "deployed"
    assert (target_skills / "tdd").is_symlink()


def test_idempotent_redeploy_replaces_symlink_and_returns_deployed(tmp_path):
    source_dir = _make_skill_dir(tmp_path / "repo" / "skills")
    target_skills = tmp_path / ".claude" / "skills"
    target_skills.mkdir(parents=True)
    reconcile_skill(source_dir, target_skills)

    result = reconcile_skill(source_dir, target_skills)

    assert result == "deployed"
    link = target_skills / "tdd"
    assert link.is_symlink()
    assert link.resolve() == source_dir.resolve()
