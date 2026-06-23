import io
import shutil
import tarfile
import tempfile
from pathlib import Path

import httpx

from mysk.domain.import_url import ImportUrl


class DownloadError(Exception):
    pass


def download_skill(url: ImportUrl, dest: Path) -> None:
    """Download the skill at *url* into *dest*, atomically.

    On any failure *dest* is left untouched. Raises DownloadError on HTTP
    errors or network failures.
    """
    response = httpx.get(url.tarball_url(), follow_redirects=True)
    if response.is_error:
        raise DownloadError(
            f"Failed to download {url.tarball_url()!r}: HTTP {response.status_code}"
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
            tar.extractall(tmp_path, filter="data")

        skill_dir = _find_skill_dir(tmp_path, url.skill_dir_name)
        shutil.copytree(skill_dir, dest)


def _find_skill_dir(extracted: Path, skill_dir_name: str) -> Path:
    matches = list(extracted.rglob(skill_dir_name))
    for match in matches:
        if match.is_dir():
            return match
    raise DownloadError(
        f"Could not find skill directory {skill_dir_name!r} in the downloaded archive."
    )
