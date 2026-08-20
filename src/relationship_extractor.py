"""
HTAD-10 Relationship Extraction Layer

Pipeline:

    Evidence
       ↓
    Sentence segmentation
       ↓
    Entity extraction
       ↓
    Co-occurrence filtering
       ↓
    Biomedical AI relation extraction
       ↓
    Confidence filtering
       ↓
    Structured relationships
       ↓
    Evidence Graph

The AI model interprets relationships.
The EvidenceGraph performs the higher-level inference.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .target_extractor import find_targets
from .signal_extractor import find_drugs, find_diseases
from .ai_relation import analyze_relationship
from .entity_resolver import resolve_drug, resolve_disease

# ============================================================
# Configuration
# ============================================================

AI_CONFIDENCE_THRESHOLD = 0.70

# Relations that should never create an evidence edge.
WEAK_RELATIONS = {
    "unknown",
    "none",
    "no_relation",
    "unrelated",
}

# Strong mechanistic relations.
MECHANISTIC_RELATIONS = {
    "activates",
    "inhibits",
    "binds",
    "interacts_with",
    "targets",
    "agonizes",
    "antagonizes",
    "modulates",
    "upregulates",
    "downregulates",
    "increases",
    "decreases",
}

# Valid relationship classes for target → disease.
# "associated_with" is important here because biomedical
# literature often describes biological association rather
# than direct causality.
TARGET_DISEASE_RELATIONS = {
    "associated_with",
    "implicated_in",
    "involved_in",
    "linked_to",
    "related_to",
    "regulates",
    "contributes_to",
    "affects",
    "influences",
    "mediates",
    "promotes",
    "protects_against",
    "exacerbates",
}

# ============================================================
# Sentence segmentation
# ============================================================

def split_sentences(text: str) -> List[str]:
    """
    Split biomedical text into reasonably sized sentences.

    Lightweight splitter; no external NLP dependency required.
    """

    if not text:
        return []

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) >= 20
    ]


# ============================================================
# Entity matching
# ============================================================

def _entity_in_sentence(
    entity: str,
    sentence: str,
) -> bool:
    """
    Case-insensitive biomedical entity matching.
    """

    if not entity or not sentence:
        return False

    entity_lower = entity.strip().lower()
    sentence_lower = sentence.lower()

    return entity_lower in sentence_lower


def _entities_in_sentence(
    entities: List[str],
    sentence: str,
) -> List[str]:

    return [
        entity
        for entity in entities
        if _entity_in_sentence(
            entity,
            sentence,
        )
    ]


# ============================================================
# Strict sentence selection
# ============================================================

def find_supporting_sentences(
    text: str,
    entity1: str,
    entity2: str,
) -> List[str]:
    """
    Return sentences in which BOTH entities occur.

    Used for:
        Drug → Target
        Drug → Disease

    This reduces false positives.
    """

    sentences = split_sentences(text)

    matches = []

    for sentence in sentences:

        if (
            _entity_in_sentence(
                entity1,
                sentence,
            )
            and
            _entity_in_sentence(
                entity2,
                sentence,
            )
        ):
            matches.append(sentence)

    return matches


# ============================================================
# Local sentence-window selection
# ============================================================

def find_local_supporting_sentences(
    text: str,
    entity1: str,
    entity2: str,
    window: int = 1,
) -> List[str]:
    """
    Find local evidence when two entities occur in nearby
    sentences rather than necessarily the same sentence.

    Example:

        Sentence 10:
            S1P receptor signaling is altered...

        Sentence 11:
            These changes are implicated in Alzheimer's disease.

    With window=1, the two sentences can be evaluated together.

    This is used ONLY for Target → Disease relationships.
    """

    sentences = split_sentences(text)

    if not sentences:
        return []

    entity1_indices = []
    entity2_indices = []

    for index, sentence in enumerate(sentences):

        if _entity_in_sentence(
            entity1,
            sentence,
        ):
            entity1_indices.append(index)

        if _entity_in_sentence(
            entity2,
            sentence,
        ):
            entity2_indices.append(index)

    matches = []

    for i in entity1_indices:

        for j in entity2_indices:

            if abs(i - j) <= window:

                start = max(
                    0,
                    min(i, j) - window,
                )

                end = min(
                    len(sentences),
                    max(i, j) + window + 1,
                )

                passage = " ".join(
                    sentences[start:end]
                )

                matches.append(passage)

    # Remove duplicates while preserving order.
    return list(
        dict.fromkeys(matches)
    )


# ============================================================
# AI relationship analysis
# ============================================================

def _analyze_pair(
    sentence: str,
    entity1: str,
    entity2: str,
) -> Optional[Dict]:
    """
    Ask the biomedical AI model to interpret one relationship.
    """

    try:

        result = analyze_relationship(
            sentence=sentence,
            entity1=entity1,
            entity2=entity2,
        )

    except Exception as exc:

        print(
            "[AI WARNING] "
            f"Could not analyze "
            f"{entity1} ↔ {entity2}: {exc}"
        )

        return None

    if not result:
        return None

    try:

        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        confidence = 0.0

    relation = str(
        result.get(
            "relation",
            "unknown",
        )
    ).strip().lower()

    # Confidence gate.
    if confidence < AI_CONFIDENCE_THRESHOLD:
        return None

    # Reject explicit non-relations.
    if relation in WEAK_RELATIONS:
        return None

    return {
        "relation": relation,
        "confidence": confidence,
        "model": result.get(
            "model"
        ),
    }


# ============================================================
# Relationship construction
# ============================================================

def _make_relationship(
    relationship_type: str,
    drug: Optional[str],
    target: Optional[str],
    disease: Optional[str],
    evidence,
    sentence: str,
    ai_result: Dict,
) -> Dict:
    """
    Construct standardized HTAD relationship.
    """

    confidence = float(
        ai_result.get(
            "confidence",
            0.0,
        )
    )

    return {
        "type": relationship_type,

        "drug": drug,

        "target": target,

        "disease": disease,

        "evidence": evidence,

        "supporting_sentence": sentence,

        "ai_relation": ai_result.get(
            "relation"
        ),

        "ai_confidence": confidence,

        "ai_model": ai_result.get(
            "model"
        ),

        "evidence_quality": (
            "high"
            if confidence >= 0.90
            else "moderate"
        ),
    }


# ============================================================
# Duplicate prevention
# ============================================================

def _relationship_key(
    relationship: Dict,
) -> Tuple:

    return (
        relationship.get(
            "type"
        ),

        (
            relationship.get(
                "drug"
            )
            or ""
        ).lower(),

        (
            relationship.get(
                "target"
            )
            or ""
        ).lower(),

        (
            relationship.get(
                "disease"
            )
            or ""
        ).lower(),

        (
            relationship.get(
                "ai_relation"
            )
            or ""
        ).lower(),
    )


# ============================================================
# Main extraction function
# ============================================================
def _resolve_query_entities(
    drug_query: str = "",
    disease_query: str = "",
) -> Tuple[Optional[str], Optional[str]]:

    resolved_drug = None
    resolved_disease = None

    # --------------------------------------------------------
    # Drug
    # --------------------------------------------------------

    if drug_query:

        result = resolve_drug(
            drug_query
        )

        if result:

            resolved_drug = (
                result.get(
                    "canonical_name"
                )
            )

    # --------------------------------------------------------
    # Disease
    # --------------------------------------------------------

    if disease_query:

        result = resolve_disease(
            disease_query
        )

        if result:

            resolved_disease = (
                result.get(
                    "canonical_name"
                )
            )

    return (
        resolved_drug,
        resolved_disease,
    )


def extract_relationships(
    evidence,
    drug_query="",
    disease_query="",
) -> List[Dict]:
    """
    Extract AI-verified relationships from ONE Evidence object.

    Returns:

        Drug → Target
        Target → Disease
        Drug → Disease

    Evidence strategy:

        Drug → Target
            strict same-sentence evidence

        Target → Disease
            local sentence-window evidence

        Drug → Disease
            strict same-sentence evidence
    """

    # ========================================================
    # Build text
    # ========================================================

    title = evidence.title or ""
    abstract = evidence.abstract or ""

    text = ". ".join(
        part.strip().rstrip(".")
        for part in (
            title,
            abstract,
        )
        if part.strip()
    ).strip() + "."

    if not text:
        return []

    # ========================================================
    # Resolve user query entities
    # ========================================================

    resolved_drug, resolved_disease = (
        _resolve_query_entities(
            drug_query,
            disease_query,
        )
    )

    # ========================================================
    # Extract entities from literature
    # ========================================================

    drugs = list(
        dict.fromkeys(
            find_drugs(text)
        )
    )

    diseases = list(
        dict.fromkeys(
            find_diseases(text)
        )
    )

    # ========================================================
    # Force the resolved query entities into the candidate set
    # ========================================================

    if resolved_drug:
        drugs.insert(
            0,
            resolved_drug,
        )

    if resolved_disease:
        diseases.insert(
            0,
            resolved_disease,
        )

    # Remove duplicates
    drugs = list(
        dict.fromkeys(drugs)
    )

    diseases = list(
        dict.fromkeys(diseases)
    )

    targets = list(
        dict.fromkeys(
            find_targets(text)
        )
    )

    relationships = []

    seen = set()

    # ========================================================
    # DRUG → TARGET
    # ========================================================

    for drug in drugs:

        for target in targets:

            supporting_sentences = (
                find_supporting_sentences(
                    text,
                    drug,
                    target,
                )
            )

            for sentence in supporting_sentences:

                ai_result = _analyze_pair(
                    sentence=sentence,
                    entity1=drug,
                    entity2=target,
                )

                if ai_result is None:
                    continue

                relationship = _make_relationship(
                    relationship_type="drug_target",
                    drug=drug,
                    target=target,
                    disease=None,
                    evidence=evidence,
                    sentence=sentence,
                    ai_result=ai_result,
                )

                key = _relationship_key(
                    relationship
                )

                if key in seen:
                    continue

                seen.add(key)

                relationships.append(
                    relationship
                )

    # ========================================================
    # TARGET → DISEASE
    # ========================================================

    for target in targets:

        for disease in diseases:

            # IMPORTANT:
            # Unlike Drug → Target, we allow nearby sentences.
            supporting_sentences = (
                find_local_supporting_sentences(
                    text,
                    target,
                    disease,
                    window=1,
                )
            )

            for sentence in supporting_sentences:

                ai_result = _analyze_pair(
                    sentence=sentence,
                    entity1=target,
                    entity2=disease,
                )

                if ai_result is None:
                    continue

                relation = (
                    ai_result
                    .get(
                        "relation",
                        "",
                    )
                    .strip()
                    .lower()
                )

                # Target → Disease needs a biologically
                # meaningful relation. We do not accept
                # arbitrary classifier outputs here.
                if relation not in (
                    TARGET_DISEASE_RELATIONS
                    | MECHANISTIC_RELATIONS
                ):
                    continue

                relationship = _make_relationship(
                    relationship_type="target_disease",
                    drug=None,
                    target=target,
                    disease=disease,
                    evidence=evidence,
                    sentence=sentence,
                    ai_result=ai_result,
                )

                key = _relationship_key(
                    relationship
                )

                if key in seen:
                    continue

                seen.add(key)

                relationships.append(
                    relationship
                )

    # ========================================================
    # DRUG → DISEASE
    # ========================================================

    for drug in drugs:

        for disease in diseases:

            supporting_sentences = (
                find_supporting_sentences(
                    text,
                    drug,
                    disease,
                )
            )

            for sentence in supporting_sentences:

                ai_result = _analyze_pair(
                    sentence=sentence,
                    entity1=drug,
                    entity2=disease,
                )

                if ai_result is None:
                    continue

                relationship = _make_relationship(
                    relationship_type="drug_disease",
                    drug=drug,
                    target=None,
                    disease=disease,
                    evidence=evidence,
                    sentence=sentence,
                    ai_result=ai_result,
                )

                key = _relationship_key(
                    relationship
                )

                if key in seen:
                    continue

                seen.add(key)

                relationships.append(
                    relationship
                )

    # ========================================================
    # Sort strongest relationships first
    # ========================================================

    relationships.sort(
        key=lambda x: (
            x.get(
                "ai_confidence",
                0.0,
            ),

            1
            if x.get("type")
            == "drug_target"
            else 0,
        ),
        reverse=True,
    )

    return relationships