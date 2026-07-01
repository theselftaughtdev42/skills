from pathlib import Path

from mysk.domain import LifecycleState, MyskBlock, Skill
from mysk.io.targets import Target, discover_targets, is_deployed


def test_target_label_uses_tilde_for_home_relative_paths():
    p = Path.home() / ".claude" / "skills"
    t = Target(name="claude", path=p)
    assert t.label() == "~/.claude/skills (claude)"


def test_target_label_uses_absolute_path_when_not_under_home():
    t = Target(name="claude", path=Path("/var/skills"))
    assert t.label() == "/var/skills (claude)"


def test_is_deployed_false_when_symlink_points_outside_library(tmp_path):
    library = tmp_path / "library"
    elsewhere = tmp_path / "elsewhere" / "foo"
    elsewhere.mkdir(parents=True)
    skill = Skill(
        name="foo",
        description="d",
        mysk=MyskBlock(state=LifecycleState.ACTIVE),
    )
    target = Target(name="claude", path=tmp_path / "target")
    target.path.mkdir()
    (target.path / "foo").symlink_to(elsewhere)

    assert is_deployed(target, skill, library) is False


def test_discover_targets_returns_agent_when_home_dir_exists(tmp_path):
    (tmp_path / ".claude").mkdir()

    targets = discover_targets(search_root=tmp_path)

    assert len(targets) == 1
    assert targets[0].name == "claude"
    assert targets[0].path == tmp_path / ".claude" / "skills"


def test_discover_targets_returns_agent_when_home_and_skills_dir_both_exist(tmp_path):
    (tmp_path / ".claude" / "skills").mkdir(parents=True)

    targets = discover_targets(search_root=tmp_path)

    assert len(targets) == 1
    assert targets[0].name == "claude"


def test_discover_targets_excludes_agent_when_home_dir_missing(tmp_path):
    targets = discover_targets(search_root=tmp_path)

    assert targets == []


def test_is_deployed_true_when_skill_link_points_into_library(tmp_path):
    library = tmp_path / "library"
    skill_source = library / "foo"
    skill_source.mkdir(parents=True)
    skill = Skill(
        name="foo",
        description="d",
        mysk=MyskBlock(state=LifecycleState.ACTIVE),
    )
    target = Target(name="claude", path=tmp_path / "target")
    target.path.mkdir()
    (target.path / "foo").symlink_to(skill_source)

    assert is_deployed(target, skill, library) is True


def test_is_deployed_false_when_no_entry_at_target(tmp_path):
    library = tmp_path / "library"
    skill = Skill(
        name="foo",
        description="d",
        mysk=MyskBlock(state=LifecycleState.ACTIVE),
    )
    target = Target(name="claude", path=tmp_path / "target")
    target.path.mkdir()

    assert is_deployed(target, skill, library) is False


def test_is_deployed_false_when_entry_is_plain_directory(tmp_path):
    library = tmp_path / "library"
    skill = Skill(
        name="foo",
        description="d",
        mysk=MyskBlock(state=LifecycleState.ACTIVE),
    )
    target = Target(name="claude", path=tmp_path / "target")
    target.path.mkdir()
    (target.path / "foo").mkdir()

    assert is_deployed(target, skill, library) is False
