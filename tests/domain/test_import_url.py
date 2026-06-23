import pytest

from mysk.domain.import_url import ImportUrl


def test_parse_valid_url():
    url = ImportUrl.parse(
        "https://github.com/alice/cool-skills/tree/main/skills/my-skill"
    )

    assert url.owner == "alice"
    assert url.repo == "cool-skills"
    assert url.ref == "main"
    assert url.path == "skills/my-skill"
    assert url.skill_dir_name == "my-skill"


def test_parse_rejects_non_github_host():
    with pytest.raises(ValueError, match="Only github.com URLs are supported"):
        ImportUrl.parse(
            "https://gitlab.com/alice/cool-skills/tree/main/skills/my-skill"
        )


def test_parse_rejects_malformed_url():
    with pytest.raises(ValueError, match="Expected a GitHub URL of the form"):
        ImportUrl.parse("https://github.com/alice/cool-skills")
