import pydantic
import pytest

from mysk.domain import Provenance


def test_default_provenance_is_self_authored():
    assert Provenance().is_imported is False


def test_skill_with_source_is_imported():
    prov = Provenance(source="https://github.com/owner/repo", modified=True)

    assert prov.is_imported is True
    assert prov.source == "https://github.com/owner/repo"
    assert prov.modified is True


def test_provenance_rejects_non_bool_modified():
    with pytest.raises(pydantic.ValidationError):
        Provenance(source="https://x", modified="definitely")


def test_provenance_stores_upstream_name():
    prov = Provenance(source="https://github.com/a/b", upstream_name="original-name")

    assert prov.upstream_name == "original-name"


def test_provenance_upstream_name_defaults_to_none():
    assert Provenance().upstream_name is None
