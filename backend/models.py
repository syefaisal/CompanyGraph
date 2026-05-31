from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class NodeCreate(BaseModel):
    label: str = Field(..., description="Node label: Person, Product, Customer, Workflow, or Decision")
    properties: dict[str, Any] = Field(..., description="Node properties (name is required)")


class RelationshipCreate(BaseModel):
    from_id: str
    to_id: str
    rel_type: str = Field(..., description="e.g. WORKS_ON, USES, MADE, AFFECTS, INVOLVES, DEPENDS_ON")
    properties: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    keyword: str
    label: Optional[str] = None
