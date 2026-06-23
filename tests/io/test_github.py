import io
import tarfile

import httpx
import pytest
import respx

from mysk.domain.import_url import ImportUrl
from mysk.io.github import DownloadError, download_skill

_URL = ImportUrl.parse("https://github.com/alice/cool-skills/tree/main/skills/my-skill")


@respx.mock
def test_download_failure_raises_and_writes_no_files(tmp_path):
    respx.get(_URL.tarball_url()).mock(return_value=httpx.Response(404))

    with pytest.raises(DownloadError, match="404"):
        download_skill(_URL, tmp_path / "my-skill")

    assert not (tmp_path / "my-skill").exists()


def _make_tarball(skill_dir_name: str, files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel_path, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name=f"repo-abc123/{skill_dir_name}/{rel_path}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


@respx.mock
def test_download_extracts_skill_files(tmp_path):
    tarball = _make_tarball(
        "my-skill",
        {"SKILL.md": "---\nname: my-skill\n---\n# body\n", "helper.py": "pass\n"},
    )
    respx.get(_URL.tarball_url()).mock(
        return_value=httpx.Response(200, content=tarball)
    )

    dest = tmp_path / "my-skill"
    download_skill(_URL, dest)

    assert (dest / "SKILL.md").read_text() == "---\nname: my-skill\n---\n# body\n"
    assert (dest / "helper.py").read_text() == "pass\n"
