from mysk.io.skills import skill_library_path


def library_cmd() -> None:
    """Print the Skill Library filepath."""
    print(skill_library_path())
