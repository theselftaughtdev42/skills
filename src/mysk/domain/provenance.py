from __future__ import annotations

import pydantic


class Provenance(pydantic.BaseModel):
    """Whether a skill is self-authored or imported from an external source.

    A `source` URL marks the skill as imported; `modified` tracks whether the
    local copy has drifted from upstream. Self-authored skills carry neither.
    """

    model_config = pydantic.ConfigDict(frozen=True)

    source: str | None = None
    modified: bool = False

    @property
    def is_imported(self) -> bool:
        return self.source is not None
