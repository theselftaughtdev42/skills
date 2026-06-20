import shutil
from pathlib import Path
from typing import Literal

DeployOutcome = Literal["deployed", "overwritten", "skipped"]


def reconcile_skill(
    source_dir: Path, target_path: Path, overwrite: bool
) -> DeployOutcome:
    if target_path.is_symlink():
        target_path.unlink()
        target_path.symlink_to(source_dir)
        return "overwritten"

    if not target_path.exists():
        target_path.symlink_to(source_dir)
        return "deployed"

    if not overwrite:
        return "skipped"

    shutil.rmtree(target_path)
    target_path.symlink_to(source_dir)
    return "overwritten"
