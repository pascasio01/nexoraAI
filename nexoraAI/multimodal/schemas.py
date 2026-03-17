import base64
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AnalyzeInputRequest(BaseModel):
    input_type: Literal["image", "document"]
    content_base64: str = Field(min_length=1, description="Base64-encoded image/document bytes.")
    analysis_goal: str = Field(min_length=3, max_length=500)
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    public_context: Optional[str] = Field(default=None, max_length=1000)
    observed_text: Optional[str] = Field(default=None, max_length=5000)
    observed_objects: List[str] = Field(default_factory=list)

    @field_validator("content_base64")
    @classmethod
    def validate_content_base64(cls, value: str) -> str:
        try:
            raw = base64.b64decode(value, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("content_base64 must be valid base64 data.") from exc
        if not raw:
            raise ValueError("content_base64 cannot be empty.")
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError("content_base64 exceeds the 5MB temporary processing limit.")
        return value


class KnowledgeEntity(BaseModel):
    name: str
    entity_type: str
    evidence: str


class KnowledgeRelationship(BaseModel):
    source: str
    target: str
    relation: str


class AnalyzeInputResponse(BaseModel):
    structured_summary: dict
    key_findings: List[str]
    possible_interpretations: List[str]
    confidence_score: Literal["low", "medium", "high"]
    confidence_explanation: str
    knowledge_graph: dict
    privacy: dict
