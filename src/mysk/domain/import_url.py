from typing import Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict


class ImportUrl(BaseModel):
    model_config = ConfigDict(frozen=True)

    owner: str
    repo: str
    ref: str
    path: str

    @property
    def skill_dir_name(self) -> str:
        return self.path.rstrip("/").split("/")[-1]

    @classmethod
    def parse(cls, raw: str) -> Self:
        parsed = urlparse(raw)
        if parsed.hostname != "github.com":
            raise ValueError(
                f"Only github.com URLs are supported in this version, "
                f"got: {parsed.hostname!r}"
            )
        parts = parsed.path.strip("/").split("/")
        # Expected: {owner}/{repo}/tree/{ref}/{path...}
        if len(parts) < 5 or parts[2] != "tree":
            raise ValueError(
                f"Expected a GitHub URL of the form "
                f"https://github.com/{{owner}}/{{repo}}/tree/{{ref}}/{{path}}, "
                f"got: {raw!r}"
            )
        owner, repo, _, ref, *path_parts = parts
        return cls(owner=owner, repo=repo, ref=ref, path="/".join(path_parts))

    def tarball_url(self) -> str:
        return (
            f"https://api.github.com/repos/{self.owner}/{self.repo}/tarball/{self.ref}"
        )
