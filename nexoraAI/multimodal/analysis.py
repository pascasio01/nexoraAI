import base64
import re
from dataclasses import dataclass
from typing import List, Tuple

from .schemas import AnalyzeInputRequest, AnalyzeInputResponse, KnowledgeEntity, KnowledgeRelationship


class GuardrailViolation(ValueError):
    pass


@dataclass(frozen=True)
class _ConfidenceDecision:
    score: str
    explanation: str


_BLOCKED_PATTERNS = (
    "identify this person",
    "identify this face",
    "who is this person",
    "facial recognition",
    "track this person",
    "stalk",
    "dox",
    "private address",
    "private phone",
    "social security",
)


def _validate_guardrails(request: AnalyzeInputRequest) -> None:
    content = " ".join(
        filter(
            None,
            [
                request.analysis_goal.lower(),
                (request.public_context or "").lower(),
                (request.observed_text or "").lower(),
            ],
        )
    )
    if any(pattern in content for pattern in _BLOCKED_PATTERNS):
        raise GuardrailViolation(
            "Request rejected by ethical guardrails: identity tracking, stalking, and private data access are not allowed."
        )


def _extract_document_text(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8", errors="ignore").strip()


def _extract_entities(text: str, objects: List[str]) -> List[KnowledgeEntity]:
    entities: List[KnowledgeEntity] = []
    seen = set()

    for obj in objects:
        normalized = obj.strip().lower()
        if normalized and ("object", normalized) not in seen:
            entities.append(KnowledgeEntity(name=obj.strip(), entity_type="object", evidence="Visible object label"))
            seen.add(("object", normalized))

    for token in re.findall(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b", text):
        normalized = token.lower()
        if ("term", normalized) not in seen:
            entities.append(KnowledgeEntity(name=token, entity_type="term", evidence="Detected from visible text"))
            seen.add(("term", normalized))

    for date in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text):
        if ("date", date) not in seen:
            entities.append(KnowledgeEntity(name=date, entity_type="date", evidence="Detected from visible text"))
            seen.add(("date", date))

    return entities


def _build_relationships(entities: List[KnowledgeEntity], input_type: str) -> List[KnowledgeRelationship]:
    relationships: List[KnowledgeRelationship] = []
    if not entities:
        return relationships
    root = f"{input_type}_input"
    for entity in entities:
        relationships.append(
            KnowledgeRelationship(source=root, target=entity.name, relation="contains_visible_feature")
        )
    return relationships


def _confidence(visible_text: str, objects: List[str], entity_count: int) -> _ConfidenceDecision:
    evidence_points = 0
    if visible_text:
        evidence_points += 1
    if objects:
        evidence_points += 1
    if entity_count >= 4:
        evidence_points += 1

    if evidence_points >= 3:
        return _ConfidenceDecision("high", "Multiple corroborating visible signals were available.")
    if evidence_points == 2:
        return _ConfidenceDecision("medium", "Findings are based on partial but consistent visible evidence.")
    return _ConfidenceDecision("low", "Limited visible evidence was available for analysis.")


def _build_findings(
    request: AnalyzeInputRequest, visible_text: str, entities: List[KnowledgeEntity]
) -> Tuple[List[str], List[str], str]:
    findings = [
        f"Input type processed: {request.input_type}.",
        "No facial recognition or real-person identification was performed.",
        "Data was processed in-memory and marked for immediate disposal.",
    ]

    if visible_text:
        findings.append("Visible text signals were extracted from the submitted content.")
    if request.observed_objects:
        findings.append("Visible object labels were included in the analysis.")
    if entities:
        findings.append(f"Knowledge graph includes {len(entities)} extracted entities.")

    interpretations = [
        "The content appears suitable for professional or technical review.",
        "Entity relationships may support indexing, categorization, or compliance workflows.",
    ]
    if not entities:
        interpretations.append("Additional visible text or object context could improve interpretability.")

    summary = (
        f"Analyzed {request.input_type} input for technical insights while enforcing privacy and ethical guardrails."
    )
    return findings, interpretations, summary


def analyze_multimodal_input(request: AnalyzeInputRequest) -> AnalyzeInputResponse:
    _validate_guardrails(request)

    temp_buffer = bytearray(base64.b64decode(request.content_base64, validate=True))
    try:
        visible_text = (request.observed_text or "").strip()
        if request.input_type == "document" and not visible_text:
            visible_text = _extract_document_text(bytes(temp_buffer))

        entities = _extract_entities(visible_text, request.observed_objects)
        relationships = _build_relationships(entities, request.input_type)
        confidence = _confidence(visible_text, request.observed_objects, len(entities))
        key_findings, interpretations, summary = _build_findings(request, visible_text, entities)

        return AnalyzeInputResponse(
            structured_summary={
                "summary": summary,
                "input_type": request.input_type,
                "visible_text_excerpt": visible_text[:280],
                "visible_objects": request.observed_objects,
            },
            key_findings=key_findings,
            possible_interpretations=interpretations,
            confidence_score=confidence.score,
            confidence_explanation=confidence.explanation,
            knowledge_graph={
                "entities": [entity.model_dump() for entity in entities],
                "relationships": [relationship.model_dump() for relationship in relationships],
            },
            privacy={
                "data_retention": "temporary_only",
                "image_document_storage": "not_persisted",
            },
        )
    finally:
        for index in range(len(temp_buffer)):
            temp_buffer[index] = 0
