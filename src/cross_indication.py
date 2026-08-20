"""KNOWN_INDICATIONS = {
    "siponimod": {
        "multiple sclerosis"
    },

    "itraconazole": {
        "fungal infections"
    },

    "anastrozole": {
        "breast cancer"
    },

    "letrozole": {
        "breast cancer"
    },

    "exemestane": {
        "breast cancer"
    },
}
def detect_cross_indication(signal):

    existing = KNOWN_INDICATIONS.get(
        signal.drug,
        set()
    )

    new_disease = signal.disease.lower()

    if new_disease in existing:
        return None

    return {
        "drug": signal.drug,
        "existing_indications": list(existing),
        "new_indication": new_disease,
        "target": signal.target,
        "evidence": signal.evidence,
    }"""

KNOWN_INDICATIONS = {

    "siponimod": {
        "multiple sclerosis"
    },

    "anastrozole": {
        "breast cancer"
    },

    "letrozole": {
        "breast cancer"
    },

    "exemestane": {
        "breast cancer"
    },

    "itraconazole": {
        "fungal infections"
    },
}


def detect_cross_indication(signal):

    existing = KNOWN_INDICATIONS.get(
        signal.drug.lower(),
        set()
    )

    new_indication = signal.disease.lower()

    # Unknown drug → we cannot establish
    # cross-indication status yet.
    if not existing:
        return None

    # Already an existing indication.
    if new_indication in existing:
        return None

    return {
        "drug": signal.drug,
        "existing_indications": sorted(existing),
        "new_indication": signal.disease,
        "target": signal.target,
        "evidence_score": signal.evidence_score,
        "evidence": signal.evidence,
    }