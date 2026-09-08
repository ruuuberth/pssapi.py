from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class PssModel(BaseModel):
    """Base model that keeps unknown API fields for forward compatibility."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        validate_assignment=True,
    )

    def raw(self) -> dict[str, Any]:
        """Return the complete model payload, including unknown fields."""
        return self.model_dump(by_alias=True, exclude_none=False)
