import pytest

from mysk.domain.naming import validate_skill_name


def test_valid_name_passes():
    validate_skill_name("my-skill")


def test_name_with_uppercase_fails():
    with pytest.raises(ValueError, match="lowercase letters and hyphens"):
        validate_skill_name("My-Skill")


def test_name_with_digits_fails():
    with pytest.raises(ValueError, match="lowercase letters and hyphens"):
        validate_skill_name("skill-2")


def test_name_with_underscore_fails():
    with pytest.raises(ValueError, match="lowercase letters and hyphens"):
        validate_skill_name("my_skill")


def test_name_exceeding_64_chars_fails():
    with pytest.raises(ValueError, match="64 characters"):
        validate_skill_name("a" * 65)


def test_name_of_exactly_64_chars_passes():
    validate_skill_name("a" * 64)
