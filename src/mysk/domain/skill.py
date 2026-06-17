from __future__ import annotations

import pydantic

from mysk.domain.lifecycle import LifecycleState
from mysk.domain.mysk_block import MyskBlock
from mysk.domain.provenance import Provenance


class Skill(pydantic.BaseModel):
    """A skill: generic identity, plus an optional mysk block when owned.

    `name`/`description` are generic frontmatter any agent reads. `mysk` is
    present only once the skill has been adopted (migrated) into mysk
    management; an un-migrated skill carries no block (`mysk is None`).
    """

    model_config = pydantic.ConfigDict(frozen=True)

    name: str
    description: str
    mysk: MyskBlock | None = None

    @classmethod
    def from_frontmatter(cls, data: dict) -> Skill:
        """Build a Skill from a parsed frontmatter dict (inverse of to_frontmatter).

        A skill with no `mysk` key is un-migrated and gets `mysk=None`. When the
        `mysk` block is present it must carry a `state` — otherwise it is
        malformed and a ValueError is raised. Adding the block is the migrate
        command's job, never this layer's.
        """
        block = None
        if "mysk" in data:
            raw = data["mysk"]
            if not isinstance(raw, dict) or "state" not in raw:
                raise ValueError(
                    "mysk block exists but is missing required 'state' key"
                )
            block = MyskBlock(
                state=LifecycleState(raw["state"]),
                provenance=Provenance(
                    source=raw.get("source"),
                    modified=raw.get("modified", False),
                ),
            )
        return cls(name=data["name"], description=data["description"], mysk=block)

    def to_frontmatter(self) -> dict:
        """Render to a frontmatter dict: generic fields, plus the `mysk` block only
        if the skill is owned. An un-migrated skill emits no `mysk` key.
        """
        result: dict = {"name": self.name, "description": self.description}
        if self.mysk is not None:
            block: dict = {"state": self.mysk.state.value}
            if self.mysk.provenance.is_imported:
                block["source"] = self.mysk.provenance.source
                block["modified"] = self.mysk.provenance.modified
            result["mysk"] = block
        return result
