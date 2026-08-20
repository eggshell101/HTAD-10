"""
HTAD-10 Live Evidence Discovery Pipeline

Live sources:
    - PubMed
    - ClinicalTrials.gov
    - medRxiv

The pipeline performs:
    1. Live evidence retrieval
    2. Relevance filtering
    3. Lightweight relationship extraction
    4. Evidence graph construction
    5. Repurposing candidate inference
    6. HTAD scoring
    7. GUI-ready output
"""

import re
from collections import defaultdict
from typing import List, Dict, Any

from .pubmed import search_pubmed
from .biorxiv import search_preprints
from .clinicaltrials import fetch_trials
from .ai_relation import analyze_relationship
from .relationship_extractor import extract_relationships
from .models import Evidence
from .quantum_validator import validate_candidate


# ============================================================
# KNOWN INDICATIONS
# ============================================================

KNOWN_INDICATIONS = {
    "siponimod": {
        "multiple sclerosis",
        "ms",
    },

    "metformin": {
        "type 2 diabetes",
        "diabetes",
    },

    "atorvastatin": {
        "hypercholesterolemia",
        "cardiovascular disease",
        "hyperlipidemia",
    },

    "thalidomide": {
        "multiple myeloma",
        "leprosy",
    },

    "anastrozole": {
        "breast cancer",
    },

    "letrozole": {
        "breast cancer",
    },

    "exemestane": {
        "breast cancer",
    },
}


# ============================================================
# TARGET PATTERNS
# ============================================================

TARGET_PATTERNS = [
    r"\bS1P receptor\b",
    r"\bsphingosine[- ]1[- ]phosphate receptor\b",
    r"\bAMPK\b",
    r"\bAMP-activated protein kinase\b",
    r"\bJAK\b",
    r"\bJAK1\b",
    r"\bJAK2\b",
    r"\bJAK3\b",
    r"\bPD-1\b",
    r"\bPD-L1\b",
    r"\bEGFR\b",
    r"\bCOX[- ]2\b",
    r"\bCOX2\b",
    r"\bCereblon\b",
]


# ============================================================
# HELPERS
# ============================================================

def normalize(text: str) -> str:

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text.strip().lower(),
    )

def _matches_entity(query: str, value: str) -> bool:
    """
    Flexible biomedical entity matching.

    Handles cases such as:

        Alzheimer's
        Alzheimer's disease

        Alzheimer
        Alzheimer disease

        MS
        multiple sclerosis
    """

    query = normalize(query)
    value = normalize(value)

    if not query or not value:
        return False

    if query == value:
        return True

    if query in value:
        return True

    if value in query:
        return True

    # Common Alzheimer's variants
    alzheimer_variants = {
        "alzheimer",
        "alzheimer's",
        "alzheimer disease",
        "alzheimer's disease",
        "ad",
    }

    if (
        query in alzheimer_variants
        and value in alzheimer_variants
    ):
        return True

    return False

def clean_target(target: str) -> str:

    target = target.strip()

    replacements = {
        "s1p receptor": "S1P receptor",
        "sphingosine-1-phosphate receptor":
            "S1P receptor",
        "amp": "AMPK",
        "amp-activated protein kinase":
            "AMPK",
        "cereblon": "Cereblon",
        "egfr": "EGFR",
        "pd-1": "PD-1",
        "pd-l1": "PD-L1",
        "jak": "JAK",
        "jak1": "JAK1",
        "jak2": "JAK2",
        "jak3": "JAK3",
        "cox2": "COX-2",
        "cox-2": "COX-2",
    }

    return replacements.get(
        normalize(target),
        target,
    )


def extract_targets(text: str) -> List[str]:

    if not text:
        return []

    targets = []

    for pattern in TARGET_PATTERNS:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for match in matches:

            target = clean_target(
                match
            )

            if target not in targets:
                targets.append(target)

    return targets


def evidence_text(item: Dict[str, Any]) -> str:

    return normalize(
        f"{item.get('title', '')} "
        f"{item.get('abstract', '')}"
    )


# ============================================================
# RELEVANCE
# ============================================================

def is_relevant(
    item: Dict[str, Any],
    drug: str = "",
    disease: str = "",
) -> bool:

    text = evidence_text(item)

    drug_norm = normalize(drug)
    disease_norm = normalize(disease)

    drug_found = (
        not drug_norm
        or drug_norm in text
    )

    disease_found = (
        not disease_norm
        or disease_norm in text
    )

    return drug_found and disease_found


# ============================================================
# RELATIONSHIP EXTRACTION
# ============================================================

"""def _sentences(text: str) -> List[str]:
    if not text:
        return []

    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]
"""
"""
def _cooccurs_locally(text: str, a: str, b: str, window: int = 350) -> bool:
    if not a or not b:
        return False

    text = normalize(text)
    a = normalize(a)
    b = normalize(b)

    if a not in text or b not in text:
        return False

    for sentence in _sentences(text):
        if a in sentence and b in sentence:
            return True

    # Allow a short cross-sentence relationship, but not whole-document
    # co-occurrence.
    for match in re.finditer(re.escape(a), text):
        left = max(0, match.start() - window)
        right = min(len(text), match.end() + window)
        if b in text[left:right]:
            return True

    return False
"""


"""THERAPEUTIC_PATTERNS = [
    r"\brepurpos",
    r"\breposition",
    r"\boff[- ]label",
    r"\bnew indication",
    r"\bnew therapeutic",
    r"\bpotential treatment",
    r"\bpotential therapeutic",
    r"\btherapeutic potential",
    r"\btreated with",
    r"\btreatment with",
    r"\btherapy with",
    r"\befficacy of",
    r"\beffective against",
    r"\bclinical trial",
    r"\bphase (?:i|ii|iii|iv)\b",
]


def _has_therapeutic_context(text: str) -> bool:
    text = normalize(text)
    return any(re.search(pattern, text) for pattern in THERAPEUTIC_PATTERNS)


def _is_clinical_source(item: Dict[str, Any]) -> bool:
    return normalize(str(item.get("source", ""))) in {
        "clinicaltrials.gov",
        "clinicaltrials",
    }

def _entity_variants(entity: str) -> list[str]:


    entity = entity.strip()

    variants = {
        entity.lower(),
    }

    normalized = (
        entity.lower()
        .replace("-", " ")
        .replace("_", " ")
    )

    variants.add(normalized)

    # S1P receptor ↔ S1PR
    if normalized == "s1p receptor":
        variants.update({
            "s1pr",
            "s1p receptor",
            "s1pr1",
            "s1pr2",
            "s1pr3",
            "s1pr4",
            "s1pr5",
        })

    # Alzheimer's variants
    if normalized in {
        "alzheimer",
        "alzheimer's",
        "alzheimer disease",
        "alzheimer's disease",
    }:
        variants.update({
            "alzheimer",
            "alzheimer's",
            "alzheimer disease",
            "alzheimer's disease",
            "ad",
        })

    return list(variants)


def _entity_occurs(
    entity: str,
    sentence: str,
) -> bool:

    sentence_lower = sentence.lower()

    for variant in _entity_variants(entity):

        if variant in sentence_lower:
            return True

    return False


def _find_best_sentence(
    text: str,
    entity1: str,
    entity2: str,
) -> str | None:


    if not text:
        return None

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    candidates = []

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        has_entity1 = _entity_occurs(
            entity1,
            sentence,
        )

        has_entity2 = _entity_occurs(
            entity2,
            sentence,
        )

        if has_entity1 and has_entity2:

            candidates.append(
                sentence
            )

    if not candidates:
        return None

    # Prefer shorter, focused sentences.
    return min(
        candidates,
        key=len,
    )

def extract_relationships(
    evidence: List[Dict[str, Any]],
    drug_query: str = "",
    disease_query: str = "",
) -> List[Dict[str, Any]]:

    relationships = []

    drug_query_norm = normalize(drug_query)
    disease_query_norm = normalize(disease_query)

    seen = set()

    for item in evidence:

        text = evidence_text(item)

        if not text:
            continue

        # ----------------------------------------------------
        # Identify requested drug and disease
        # ----------------------------------------------------

        drug = (
            drug_query_norm
            if drug_query_norm
            and drug_query_norm in text
            else None
        )

        disease = (
            disease_query_norm
            if disease_query_norm
            and disease_query_norm in text
            else None
        )

        # ----------------------------------------------------
        # Extract targets
        # ----------------------------------------------------

        targets = extract_targets(text)

        # ====================================================
        # Drug → Target
        # ====================================================

        if drug:

            for target in targets:

                if not _cooccurs_locally(
                    text,
                    drug,
                    target,
                ):
                    continue

                # ------------------------------------------------
                # AI verification
                # ------------------------------------------------

                ai_result = None

                try:

                    # Find a useful local sentence/context.
                    support_sentence = _find_best_sentence(
                        text,
                        drug,
                        target,
                    )

                    if support_sentence:

                        ai_result = analyze_relationship(
                            sentence=support_sentence,
                            entity1=drug,
                            entity2=target,
                        )

                except Exception as exc:

                    print(
                        "[AI WARNING] "
                        f"Drug-target analysis failed: {exc}"
                    )

                # ------------------------------------------------
                # AI confidence
                # ------------------------------------------------

                ai_confidence = 0.0
                ai_relation = None
                ai_model = None

                if ai_result:

                    ai_confidence = float(
                        ai_result.get(
                            "confidence",
                            0.0,
                        )
                    )

                    ai_relation = ai_result.get(
                        "relation"
                    )

                    ai_model = ai_result.get(
                        "model"
                    )

                # Don't discard the classical relationship
                # if the AI model fails.
                relationship = {
                    "type": "drug_target",
                    "drug": drug,
                    "target": target,
                    "disease": None,
                    "evidence": item,

                    # AI evidence
                    "ai_relation": ai_relation,
                    "ai_confidence": ai_confidence,
                    "ai_model": ai_model,
                    "supporting_sentence": (
                        support_sentence
                        if support_sentence
                        else None
                    ),
                }

                key = (
                    relationship["type"],
                    drug,
                    target,
                )

                if key not in seen:

                    seen.add(key)

                    relationships.append(
                        relationship
                    )

        # ====================================================
        # Target → Disease
        # ====================================================

        if disease:

            for target in targets:

                if not _cooccurs_locally(
                    text,
                    target,
                    disease,
                ):
                    continue

                # ------------------------------------------------
                # AI verification
                # ------------------------------------------------

                ai_result = None

                try:

                    support_sentence = _find_best_sentence(
                        text,
                        target,
                        disease,
                    )

                    if support_sentence:

                        ai_result = analyze_relationship(
                            sentence=support_sentence,
                            entity1=target,
                            entity2=disease,
                        )

                except Exception as exc:

                    print(
                        "[AI WARNING] "
                        f"Target-disease analysis failed: {exc}"
                    )

                ai_confidence = 0.0
                ai_relation = None
                ai_model = None

                if ai_result:

                    ai_confidence = float(
                        ai_result.get(
                            "confidence",
                            0.0,
                        )
                    )

                    ai_relation = ai_result.get(
                        "relation"
                    )

                    ai_model = ai_result.get(
                        "model"
                    )

                relationship = {
                    "type": "target_disease",
                    "drug": None,
                    "target": target,
                    "disease": disease,
                    "evidence": item,

                    "ai_relation": ai_relation,
                    "ai_confidence": ai_confidence,
                    "ai_model": ai_model,
                    "supporting_sentence": (
                        support_sentence
                        if support_sentence
                        else None
                    ),
                }

                key = (
                    relationship["type"],
                    target,
                    disease,
                )

                if key not in seen:

                    seen.add(key)

                    relationships.append(
                        relationship
                    )

        # ====================================================
        # Drug → Disease
        # ====================================================

        if (
            drug
            and disease
            and _cooccurs_locally(
                text,
                drug,
                disease,
            )
        ):

            if (
                _has_therapeutic_context(text)
                or _is_clinical_source(item)
            ):

                support_sentence = _find_best_sentence(
                    text,
                    drug,
                    disease,
                )

                ai_result = None

                try:

                    if support_sentence:

                        ai_result = analyze_relationship(
                            sentence=support_sentence,
                            entity1=drug,
                            entity2=disease,
                        )

                except Exception as exc:

                    print(
                        "[AI WARNING] "
                        f"Drug-disease analysis failed: {exc}"
                    )

                ai_confidence = 0.0
                ai_relation = None
                ai_model = None

                if ai_result:

                    ai_confidence = float(
                        ai_result.get(
                            "confidence",
                            0.0,
                        )
                    )

                    ai_relation = ai_result.get(
                        "relation"
                    )

                    ai_model = ai_result.get(
                        "model"
                    )

                relationship = {
                    "type": "drug_disease",
                    "drug": drug,
                    "target": None,
                    "disease": disease,
                    "evidence": item,

                    "ai_relation": ai_relation,
                    "ai_confidence": ai_confidence,
                    "ai_model": ai_model,
                    "supporting_sentence": support_sentence,
                }

                key = (
                    relationship["type"],
                    drug,
                    disease,
                )

                if key not in seen:

                    seen.add(key)

                    relationships.append(
                        relationship
                    )

    return relationships
"""

# ============================================================
# GRAPH
# ============================================================

def build_graph(
    relationships: List[Dict[str, Any]]
):

    graph = defaultdict(
        lambda: defaultdict(set)
    )

    for relation in relationships:

        relationship_type = relation.get(
            "type"
        )

        drug = normalize(
            relation.get("drug") or ""
        )

        target = normalize(
            relation.get("target") or ""
        )

        disease = normalize(
            relation.get("disease") or ""
        )

        if relationship_type == "drug_target":

            if drug and target:

                graph["drug_target"][
                    drug
                ].add(
                    target
                )

        elif relationship_type == "target_disease":

            if target and disease:

                graph["target_disease"][
                    target
                ].add(
                    disease
                )

        elif relationship_type == "drug_disease":

            if drug and disease:

                graph["drug_disease"][
                    drug
                ].add(
                    disease
                )

    return graph


# ============================================================
# CANDIDATE INFERENCE
# ============================================================

def infer_candidates(
    graph,
    relationships,
    requested_drug: str = "",
    requested_disease: str = "",
):

    candidates = []

    drug_norm = normalize(requested_drug)
    disease_norm = normalize(requested_disease)

    # --------------------------------------------------------
    # TARGET-MEDIATED PATH
    # --------------------------------------------------------

    for drug, targets in graph["drug_target"].items():

        if drug_norm and not _matches_entity(
            drug_norm,
            drug,
        ):
            continue

        for target in targets:

            diseases = graph["target_disease"].get(
                target,
                set(),
            )

            for disease in diseases:

                if disease_norm and not _matches_entity(
                    disease_norm,
                    disease,
                ):
                    continue

                existing = KNOWN_INDICATIONS.get(
                    drug,
                    set(),
                )

                if disease in existing:
                    continue

                candidates.append(
                    {
                        "drug": drug,
                        "target": target,
                        "candidate_disease": disease,
                        "existing_indications": sorted(existing),
                        "candidate_type": "mechanistic",
                        "reason": (
                            f"{drug} is associated with {target}, "
                            f"which is locally associated with {disease} "
                            f"in the retrieved evidence."
                        ),
                    }
                )

    # --------------------------------------------------------
    # DIRECT DRUG -> DISEASE
    # --------------------------------------------------------
    #
    # Only relationships that passed the strict therapeutic/
    # clinical filter above can reach this section.
    # --------------------------------------------------------

    if requested_drug:

        drug = normalize(requested_drug)

        for disease in graph["drug_disease"].get(drug, set()):

            if disease_norm and disease != disease_norm:
                continue

            existing = KNOWN_INDICATIONS.get(
                drug,
                set(),
            )

            if disease in existing:
                continue

            already_exists = any(
                c["candidate_disease"] == disease
                for c in candidates
            )

            if not already_exists:
                candidates.append(
                    {
                        "drug": drug,
                        "target": None,
                        "candidate_disease": disease,
                        "existing_indications": sorted(existing),
                        "candidate_type": "direct",
                        "reason": (
                            f"{drug} has direct therapeutic or "
                            f"clinical evidence associated with "
                            f"{disease} in the retrieved sources."
                        ),
                    }
                )

    return candidates


# ============================================================
# SCORING
# ============================================================

def _same_entity(a, b):
    if not a or not b:
        return False
    return (
        str(a).strip().lower()
        == str(b).strip().lower()
    )


def _evidence_dict(item):
    if isinstance(item, dict):
        return item

    if hasattr(item, "model_dump"):
        return item.model_dump()

    if hasattr(item, "dict"):
        return item.dict()

    return item


def _is_clinical_source(item: Dict[str, Any]) -> bool:
    return normalize(
        str(item.get("source", ""))
    ) in {
        "clinicaltrials.gov",
        "clinicaltrials",
    }


def score_candidate(
    candidate: Dict[str, Any],
    relationships: List[Dict[str, Any]],
) -> Dict[str, Any]:

    drug = candidate["drug"]
    disease = candidate["candidate_disease"]
    target = candidate.get("target")
    candidate_type = candidate.get(
        "candidate_type",
        "direct",
    )

    supporting = []

    relevant_relationships = []

    # ========================================================
    # FIND SUPPORTING RELATIONSHIPS
    # ========================================================

    for relation in relationships:

        if target:

            relevant = (
                _same_entity(
                    relation.get("drug"),
                    drug,
                )
                and _same_entity(
                    relation.get("target"),
                    target,
                )
            ) or (
                _same_entity(
                    relation.get("target"),
                    target,
                )
                and _same_entity(
                    relation.get("disease"),
                    disease,
                )
            )

        else:

            relevant = (
                relation.get("type") == "drug_disease"
                and _same_entity(
                    relation.get("drug"),
                    drug,
                )
                and _same_entity(
                    relation.get("disease"),
                    disease,
                )
            )

        if relevant:

            relevant_relationships.append(
                relation
            )

            evidence = relation.get(
                "evidence"
            )

            if evidence:
                evidence = _evidence_dict(
                    evidence
                )
                supporting.append(
                    evidence
                )

    # ========================================================
    # REMOVE DUPLICATE EVIDENCE
    # ========================================================

    unique = {}

    for item in supporting:

        key = (
            item.get("source"),
            item.get("identifier")
            or item.get("title"),
        )

        unique[key] = item

    supporting = list(
        unique.values()
    )

    # ========================================================
    # SOURCE / EVIDENCE COUNTS
    # ========================================================

    source_names = {
        normalize(
            str(
                item.get(
                    "source",
                    "",
                )
            )
        )
        for item in supporting
    }

    source_count = len(
        source_names
    )

    evidence_count = len(
        supporting
    )

    clinical_trial_count = sum(
        1
        for item in supporting
        if _is_clinical_source(item)
    )

    # ========================================================
    # AI CONFIDENCE
    # ========================================================

    drug_target_confidences = []

    target_disease_confidences = []

    drug_disease_confidences = []

    for relation in relevant_relationships:

        confidence = float(
            relation.get(
                "ai_confidence",
                0.0,
            )
            or 0.0
        )

        if relation.get("type") == "drug_target":

            drug_target_confidences.append(
                confidence
            )

        elif relation.get("type") == "target_disease":

            target_disease_confidences.append(
                confidence
            )

        elif relation.get("type") == "drug_disease":

            drug_disease_confidences.append(
                confidence
            )

    ai_confidence = (
        max(drug_target_confidences)
        if drug_target_confidences
        else 0.0
    )

    target_disease_confidence = (
        max(target_disease_confidences)
        if target_disease_confidences
        else 0.0
    )

    drug_disease_confidence = (
        max(drug_disease_confidences)
        if drug_disease_confidences
        else 0.0
    )

    # ========================================================
    # CLASSICAL SCORE COMPONENTS
    # ========================================================

    if candidate_type == "mechanistic":

        drug_target_evidence = sum(
            1
            for r in relationships
            if (
                r.get("type")
                == "drug_target"
                and _same_entity(
                    r.get("drug"),
                    drug,
                )
                and _same_entity(
                    r.get("target"),
                    target,
                )
            )
        )

        target_disease_evidence = sum(
            1
            for r in relationships
            if (
                r.get("type")
                == "target_disease"
                and _same_entity(
                    r.get("target"),
                    target,
                )
                and _same_entity(
                    r.get("disease"),
                    disease,
                )
            )
        )

        mechanistic = min(
            100,
            50
            + drug_target_evidence * 15
            + target_disease_evidence * 15,
        )

        literature = min(
            100,
            25 + evidence_count * 15,
        )

        clinical = min(
            100,
            clinical_trial_count * 35,
        )

        independence = min(
            100,
            source_count * 35,
        )

    else:

        mechanistic = 0

        literature = min(
            70,
            20 + evidence_count * 15,
        )

        clinical = min(
            100,
            clinical_trial_count * 50,
        )

        independence = min(
            80,
            source_count * 25,
        )

    # ========================================================
    # CLASSICAL EVIDENCE SCORE
    # ========================================================

    evidence_score = round(
        (
            clinical * 0.30
            + literature * 0.25
            + mechanistic * 0.30
            + independence * 0.15
        ),
        2,
    )

    # ========================================================
    # STORE FEATURES FOR QUANTUM LAYER
    # ========================================================

    candidate["ai_confidence"] = (
        ai_confidence
    )

    candidate[
        "target_disease_confidence"
    ] = target_disease_confidence

    candidate[
        "drug_disease_confidence"
    ] = drug_disease_confidence

    candidate[
        "classical_score"
    ] = evidence_score

    return {
        "clinical": round(
            clinical,
            2,
        ),

        "literature": round(
            literature,
            2,
        ),

        "mechanistic": round(
            mechanistic,
            2,
        ),

        "independence": round(
            independence,
            2,
        ),

        # Filled after quantum validation
        "quantum": float(
            candidate.get(
                "quantum_score",
                0.0,
            )
            or 0.0
        ),

        "final": 0.0,

    }, supporting


# ============================================================
# GUI FORMAT
# ============================================================

def candidate_to_gui(
    candidate,
    scores,
    supporting,
):

    evidence = []

    seen = set()

    for item in supporting:

        key = (
            item.get("source"),
            item.get("identifier"),
        )

        if key in seen:
            continue

        seen.add(key)

        evidence.append(
            {
                "source": item.get(
                    "source"
                ),

                "title": item.get(
                    "title"
                ),

                "identifier": item.get(
                    "identifier"
                ),

                "date": item.get(
                    "date"
                ),

                "url": item.get(
                    "url"
                ),
            }
        )

    # ========================================================
    # QUANTUM DATA
    # ========================================================

    quantum_data = {
        "status": candidate.get(
            "quantum_status",
            "pending",
        ),

        "score": candidate.get(
            "quantum_score",
            0.0,
        ),

        "energy": candidate.get(
            "quantum_energy"
        ),

        "state": candidate.get(
            "quantum_state"
        ),

        "features": candidate.get(
            "quantum_features",
            {},
        ),

        "method": candidate.get(
            "quantum_method"
        ),

        "ai_confidence": candidate.get(
            "ai_confidence",
            0.0,
        ),

        "target_disease_confidence":
            candidate.get(
                "target_disease_confidence",
                0.0,
            ),

        "classical_score":
            candidate.get(
                "classical_score",
                0.0,
            ),
    }

    # ========================================================
    # FINAL GUI OBJECT
    # ========================================================

    return {

        "drug": candidate[
            "drug"
        ],

        "target": candidate.get(
            "target"
        ) or "Direct evidence",

        "candidate_disease":
            candidate[
                "candidate_disease"
            ],

        "existing_indications":
            candidate[
                "existing_indications"
            ],

        "reason":
            candidate[
                "reason"
            ],

        "candidate_type":
            candidate.get(
                "candidate_type",
                "direct",
            ),

        "scores": scores,

        "evidence": evidence,

        "quantum_data":
            quantum_data,
    }


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_htad(
    search_drug: str = "",
    search_disease: str = "",
    use_pubmed: bool = True,
    use_medrxiv: bool = True,
    use_clinicaltrials: bool = True,
    pubmed_limit: int = 20,
    medrxiv_limit: int = 30,
    clinicaltrials_limit: int = 20,
):

    search_drug = (
        search_drug or ""
    ).strip()

    search_disease = (
        search_disease or ""
    ).strip()

    # ========================================================
    # QUERY
    # ========================================================

    terms = []

    if search_drug:
        terms.append(
            search_drug
        )

    if search_disease:
        terms.append(
            search_disease
        )

    search_query = " AND ".join(
        terms
    )

    # ========================================================
    # LIVE SEARCH
    # ========================================================

    evidence = []

    stats = {
        "pubmed": 0,
        "medrxiv": 0,
        "clinicaltrials": 0,
    }

    errors = []

    # --------------------------------------------------------
    # PUBMED
    # --------------------------------------------------------

    if use_pubmed:

        try:

            pubmed_results = search_pubmed(
                search_query
                if search_query
                else search_drug,
                limit=pubmed_limit,
            )

            evidence.extend(
                pubmed_results
            )

            stats["pubmed"] = len(
                pubmed_results
            )

        except Exception as exc:

            errors.append(
                f"PubMed: {exc}"
            )

    # --------------------------------------------------------
    # MEDRXIV
    # --------------------------------------------------------

    if use_medrxiv:

        try:

            medrxiv_results = (
                search_preprints(
                    search_query
                    if search_query
                    else search_drug,
                    server="medrxiv",
                    days=90,
                    max_results=medrxiv_limit,
                )
            )

            evidence.extend(
                medrxiv_results
            )

            stats["medrxiv"] = len(
                medrxiv_results
            )

        except Exception as exc:

            errors.append(
                f"medRxiv: {exc}"
            )

    # --------------------------------------------------------
    # CLINICALTRIALS
    # --------------------------------------------------------

    if use_clinicaltrials:

        try:

            clinical_results = (
                fetch_trials(
                    search_query
                    if search_query
                    else search_drug,
                    page_size=
                    clinicaltrials_limit,
                )
            )

            evidence.extend(
                clinical_results
            )

            stats[
                "clinicaltrials"
            ] = len(
                clinical_results
            )

        except Exception as exc:

            errors.append(
                f"ClinicalTrials.gov: {exc}"
            )

    # ========================================================
    # DEDUPLICATE EVIDENCE
    # ========================================================

    unique_evidence = {}

    for item in evidence:

        key = (
            item.get("source"),
            item.get("identifier")
            or item.get("title"),
        )

        unique_evidence[
            key
        ] = item

    evidence = list(
        unique_evidence.values()
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    relationships = []

    for item in evidence:

        # relationship_extractor expects an Evidence object,
        # while the pipeline stores normalized evidence as dictionaries.
        evidence_obj = Evidence(
            source=item.get("source", ""),
            title=item.get("title", ""),
            abstract=item.get("abstract", ""),
            date=item.get("date"),
            identifier=item.get("identifier"),
            url=item.get("url"),
        )

        relationships.extend(
            extract_relationships(
                evidence_obj,
                search_drug,
                search_disease,
            )
        )
    for rel in relationships:

        print(
            "\nAI RELATION:",
            rel.get("type"),
            "|",
            rel.get("drug"),
            "|",
            rel.get("target"),
            "|",
            rel.get("disease"),
            "|",
            rel.get("ai_relation"),
            "|",
            rel.get("ai_confidence"),
        )

        print(
            "SUPPORT:",
            rel.get("supporting_sentence")
        )

        print(
            "FULL RELATIONSHIP:",
            rel
        )

    # ========================================================
    # GRAPH
    # ========================================================

    graph = build_graph(
        relationships
    )

    # ========================================================
    # INFERENCE
    # ========================================================

    candidates = infer_candidates(
        graph,
        relationships,
        search_drug,
        search_disease,
    )

    # ========================================================
    # CLASSICAL SCORING + QUANTUM VALIDATION
    # ========================================================

    gui_candidates = []

    for candidate in candidates:

        # ----------------------------------------------------
        # STEP 1: Calculate classical evidence score
        # ----------------------------------------------------

        scores, supporting = score_candidate(
            candidate,
            relationships,
        )

        print("\n================ SCORE AUDIT ================")
        print("DRUG:", candidate.get("drug"))
        print("TARGET:", candidate.get("target"))
        print("DISEASE:", candidate.get("candidate_disease"))
        print("CLASSICAL SCORES:", scores)
        print("SUPPORTING EVIDENCE:", len(supporting))
        print("==============================================")

        # ----------------------------------------------------
        # STEP 2: Run quantum validation
        # ----------------------------------------------------

        try:

            quantum_result = validate_candidate(
                candidate
            )

            candidate.update(
                quantum_result
            )

            scores["quantum"] = float(
                quantum_result.get(
                    "quantum_score",
                    0.0,
                )
            )

            candidate[
                "quantum_status"
            ] = quantum_result.get(
                "quantum_status",
                "prototype",
            )

        except Exception as exc:

            candidate[
                "quantum_score"
            ] = 0.0

            candidate[
                "quantum_energy"
            ] = None

            candidate[
                "quantum_state"
            ] = None

            candidate[
                "quantum_features"
            ] = {}

            candidate[
                "quantum_method"
            ] = None

            candidate[
                "quantum_status"
            ] = "error"

            scores["quantum"] = 0.0

            print(
                "[QUANTUM WARNING]",
                exc,
            )

        # ----------------------------------------------------
        # STEP 3: Combine classical + quantum
        # ----------------------------------------------------

        evidence_score = (
            scores["clinical"] * 0.30
            + scores["literature"] * 0.25
            + scores["mechanistic"] * 0.30
            + scores["independence"] * 0.15
        )

        quantum_score = scores[
            "quantum"
        ]

        print("\n========== FINAL SCORE CALCULATION ==========")
        print("clinical:", scores["clinical"])
        print("literature:", scores["literature"])
        print("mechanistic:", scores["mechanistic"])
        print("independence:", scores["independence"])
        print("quantum:", scores["quantum"])

        evidence_score = (
            scores["clinical"] * 0.30
            + scores["literature"] * 0.25
            + scores["mechanistic"] * 0.30
            + scores["independence"] * 0.15
        )

        print("CALCULATED EVIDENCE SCORE:", evidence_score)

        quantum_score = scores["quantum"]

        final_score = round(
            evidence_score * 0.90
            + quantum_score * 0.10,
            2,
        )

        print("CALCULATED FINAL SCORE:", final_score)
        print("=============================================")

        final_score = round(
            evidence_score * 0.90
            + quantum_score * 0.10,
            2,
        )

        # Direct hypotheses remain capped
        if candidate.get(
            "candidate_type"
        ) == "direct":

            final_score = min(
                final_score,
                55.0,
            )

        scores["final"] = final_score

        # ----------------------------------------------------
        # STEP 4: Convert to GUI object
        # ----------------------------------------------------

        gui_candidates.append(
            candidate_to_gui(
                candidate,
                scores,
                supporting,
            )
        )


    # ========================================================
    # SORT
    # ========================================================

    gui_candidates.sort(
        key=lambda x:
        x["scores"]["final"],
        reverse=True,
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "query": {
            "drug": search_drug,
            "disease": search_disease,
        },

        "search_query": search_query,

        "statistics": stats,

        "evidence": evidence,

        "relationships": relationships,

        "candidates": gui_candidates,

        "errors": errors,
    }


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    result = run_htad(
        search_drug="osimertinib",
        search_disease="lung cancer",
    )

    print()
    print("=" * 60)
    print("HTAD-10 LIVE SEARCH")
    print("=" * 60)

    print(
        f"PubMed: "
        f"{result['statistics']['pubmed']}"
    )

    print(
        f"medRxiv: "
        f"{result['statistics']['medrxiv']}"
    )

    print(
        f"ClinicalTrials.gov: "
        f"{result['statistics']['clinicaltrials']}"
    )

    print(
        f"Relationships: "
        f"{len(result['relationships'])}"
    )

    print(
        f"Candidates: "
        f"{len(result['candidates'])}"
    )

    for candidate in result[
        "candidates"
    ]:

        print()
        print("-" * 60)

        print(
            candidate["drug"],
            "→",
            candidate["target"],
            "→",
            candidate[
                "candidate_disease"
            ],
        )

        print(
            "Type:", candidate.get("candidate_type", "direct"),
        )

        print(
            "HTAD Score:",
            candidate["scores"]["final"],
        )