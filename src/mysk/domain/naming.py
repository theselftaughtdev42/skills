import re

_VALID_NAME = re.compile(r"^[a-z-]+$")
_MAX_LEN = 64


def validate_skill_name(name: str) -> None:
    if not _VALID_NAME.match(name):
        raise ValueError(
            f"Skill name {name!r} must contain only lowercase letters and hyphens."
        )
    if len(name) > _MAX_LEN:
        raise ValueError(
            f"Skill name {name!r} exceeds the maximum of {_MAX_LEN} characters."
        )
