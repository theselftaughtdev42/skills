import io
import tarfile

import httpx
import respx
from typer.testing import CliRunner

from mysk.cli import app

runner = CliRunner()

_SOURCE_URL = "https://github.com/alice/cool-skills/tree/main/skills/my-skill"
_TARBALL_URL = "https://api.github.com/repos/alice/cool-skills/tarball/main"

_UPSTREAM_SKILL_MD = (
    "---\nname: my-skill\ndescription: does cool things\n---\n# my-skill\n"
)


def _make_tarball(skill_path: str, skill_md: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        data = skill_md.encode()
        info = tarfile.TarInfo(name=f"repo-abc/{skill_path}/SKILL.md")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _installed_skill_md(
    name: str = "my-skill",
    description: str = "does cool things",
    state: str = "active",
    source: str = _SOURCE_URL,
    modified: bool = False,
    upstream_name: str | None = None,
) -> str:
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        "mysk:",
        f"  state: {state}",
        f"  source: {source}",
        f"  modified: {'true' if modified else 'false'}",
    ]
    if upstream_name is not None:
        lines.append(f"  upstream_name: {upstream_name}")
    lines += ["---", f"# {name}", ""]
    return "\n".join(lines)


# --- 1. No arguments --------------------------------------------------------


def test_refresh_no_args_exits_with_usage_error():
    result = runner.invoke(app, ["refresh"])

    assert result.exit_code != 0


# --- 2. Skill not found -----------------------------------------------------


def test_refresh_skill_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("MYSK_SKILLS_DIR", str(tmp_path))

    result = runner.invoke(app, ["refresh", "no-such-skill"])

    assert result.exit_code != 0
    assert "no-such-skill" in result.output


# --- 3. Self-authored skill (no source) -------------------------------------


def test_refresh_self_authored_skill_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("MYSK_SKILLS_DIR", str(tmp_path))
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: mine\nmysk:\n  state: active\n---\n"
    )

    result = runner.invoke(app, ["refresh", "my-skill"])

    assert result.exit_code != 0
    assert "imported" in result.output.lower()


# --- 4. modified: true guard ------------------------------------------------


def test_refresh_modified_true_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("MYSK_SKILLS_DIR", str(tmp_path))
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(_installed_skill_md(modified=True))

    result = runner.invoke(app, ["refresh", "my-skill"])

    assert result.exit_code != 0
    assert "modified" in result.output.lower()


# --- 5. Clean refresh -------------------------------------------------------


@respx.mock
def test_refresh_clean_updates_skill_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("MYSK_SKILLS_DIR", str(tmp_path))
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(_installed_skill_md())

    upstream_md = (
        "---\nname: my-skill\ndescription: improved description\n---\n# my-skill\n"
    )
    respx.get(_TARBALL_URL).mock(
        return_value=httpx.Response(
            200, content=_make_tarball("skills/my-skill", upstream_md)
        )
    )

    result = runner.invoke(app, ["refresh", "my-skill"])

    assert result.exit_code == 0, result.output
    text = (tmp_path / "my-skill" / "SKILL.md").read_text()
    assert "description: improved description" in text
    assert "state: active" in text
    assert f"source: {_SOURCE_URL}" in text
    assert "modified: false" in text


# --- 6. upstream_name lookup ------------------------------------------------


@respx.mock
def test_refresh_upstream_name_writes_to_local_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MYSK_SKILLS_DIR", str(tmp_path))
    skill_dir = tmp_path / "local-name"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        _installed_skill_md(name="local-name", upstream_name="my-skill")
    )

    upstream_md = (
        "---\nname: my-skill\ndescription: upstream improved\n---\n# my-skill\n"
    )
    respx.get(_TARBALL_URL).mock(
        return_value=httpx.Response(
            200, content=_make_tarball("skills/my-skill", upstream_md)
        )
    )

    result = runner.invoke(app, ["refresh", "local-name"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "local-name" / "SKILL.md").exists()
    assert not (tmp_path / "my-skill").exists()
    text = (tmp_path / "local-name" / "SKILL.md").read_text()
    assert "name: local-name" in text
    assert "description: upstream improved" in text
    assert "upstream_name: my-skill" in text


# --- 7. No changes ----------------------------------------------------------


@respx.mock
def test_refresh_no_changes_skips_write(tmp_path, monkeypatch):
    monkeypatch.setenv("MYSK_SKILLS_DIR", str(tmp_path))
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(_installed_skill_md())

    respx.get(_TARBALL_URL).mock(
        return_value=httpx.Response(
            200, content=_make_tarball("skills/my-skill", _UPSTREAM_SKILL_MD)
        )
    )

    mtime_before = (tmp_path / "my-skill" / "SKILL.md").stat().st_mtime

    result = runner.invoke(app, ["refresh", "my-skill"])

    assert result.exit_code == 0, result.output
    assert "no changes" in result.output.lower()
    assert (tmp_path / "my-skill" / "SKILL.md").stat().st_mtime == mtime_before
