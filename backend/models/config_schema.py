from __future__ import annotations

"""
Eightfold AI - Runtime Configuration Schema

Supports the assignment's configurable output requirement:
- Select a subset of fields
- Rename/remap fields from canonical paths
- Set per-field normalization
- Toggle provenance and confidence
- Choose missing value strategy (null, omit, error)
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class FieldProjection(BaseModel):
    """
    Configuration for a single field in the output projection.

    Example from assignment:
    {
        "path": "primary_email",
        "from": "emails[0]",
        "type": "string",
        "required": true
    }
    """
    path: str = Field(..., description="Output field name/path")
    source_from: Optional[str] = Field(
        default=None, alias="from",
        description="Canonical path to source the value from (e.g., 'emails[0]', 'skills[].name')"
    )
    type: str = Field(default="string", description="Expected type: string, number, boolean, string[]")
    required: bool = Field(default=False, description="Whether this field must be present")
    normalize: Optional[str] = Field(
        default=None,
        description="Normalization to apply: 'E164', 'canonical', 'lowercase', etc."
    )

    model_config = {"populate_by_name": True}


class OutputConfig(BaseModel):
    """
    Runtime output configuration.

    Controls how the canonical candidate data is projected
    into the final output without modifying the canonical record itself.
    """
    fields: list[FieldProjection] = Field(
        default_factory=list,
        description="List of field projections to include in output"
    )
    include_confidence: bool = Field(
        default=True,
        description="Whether to include overall_confidence in output"
    )
    include_provenance: bool = Field(
        default=True,
        description="Whether to include provenance entries in output"
    )
    include_analytics: bool = Field(
        default=True,
        description="Whether to include analytics in response"
    )
    on_missing: Literal["null", "omit", "error"] = Field(
        default="null",
        description="Strategy for missing required values"
    )

    def has_custom_fields(self) -> bool:
        """Return True if custom field projections are configured."""
        return len(self.fields) > 0


# Default configuration — outputs full canonical schema
DEFAULT_CONFIG = OutputConfig(
    fields=[],
    include_confidence=True,
    include_provenance=True,
    include_analytics=True,
    on_missing="null",
)

# Example custom configuration matching assignment spec
EXAMPLE_CUSTOM_CONFIG = OutputConfig(
    fields=[
        FieldProjection(path="full_name", type="string", required=True),
        FieldProjection(path="primary_email", source_from="emails[0]", type="string", required=True),
        FieldProjection(path="phone", source_from="phones[0]", type="string", normalize="E164"),
        FieldProjection(path="skills", source_from="skills[].name", type="string[]", normalize="canonical"),
    ],
    include_confidence=True,
    on_missing="null",
)
