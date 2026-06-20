import shutil
from pathlib import Path
from typing import Literal

DeployOutcome = Literal["deployed", "skipped"]


def reconcile_skill(
    source_dir: Path, target_path: Path, overwrite: bool = False
) -> DeployOutcome:
    """Symlink source_dir into target_path/<skill_name>. Idempotent.

    Returns "deployed" when the symlink was created or refreshed, "skipped"
    when a non-symlink directory exists at the destination and overwrite is False.
    """
    dest = target_path / source_dir.name

    if dest.is_symlink():
        dest.unlink()
    elif dest.exists():
        if not overwrite:
            return "skipped"
        shutil.rmtree(dest)

    dest.symlink_to(source_dir.resolve())
    return "deployed"
