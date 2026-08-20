"""
HTAD-10 scoring utilities.

This module is intentionally conservative:
- no mechanistic path => no mechanistic score
- quantum score is 0 until an actual quantum validation is supplied
- direct evidence is capped below high-confidence mechanistic candidates
"""

def calculate_scores(candidate):
    drug_target_evidence = candidate.get("drug_target_evidence", [])
    target_disease_evidence = candidate.get("target_disease_evidence", [])
    direct_evidence = candidate.get("drug_disease_evidence", [])

    independent_sources = len({
        e.source
        for e in (
            drug_target_evidence
            + target_disease_evidence
            + direct_evidence
        )
        if getattr(e, "source", None)
    })

    drug_target_count = len(drug_target_evidence)
    target_disease_count = len(target_disease_evidence)
    direct_count = len(direct_evidence)

    candidate_type = candidate.get("candidate_type", "direct")

    if candidate_type == "mechanistic":
        mechanistic = min(
            100,
            50
            + drug_target_count * 15
            + target_disease_count * 15,
        )
        literature = min(
            100,
            25 + (
                drug_target_count
                + target_disease_count
            ) * 15,
        )
    else:
        mechanistic = 0
        literature = min(
            70,
            20 + direct_count * 15,
        )

    clinical = min(
        100,
        sum(
            50
            for e in direct_evidence
            if str(getattr(e, "source", "")).lower()
            in {"clinicaltrials.gov", "clinicaltrials"}
        ),
    )

    independence = min(
        100,
        independent_sources * 35,
    )

    quantum = candidate.get("quantum_score", 0) or 0

    evidence_score = round(
        clinical * 0.30
        + literature * 0.25
        + mechanistic * 0.30
        + independence * 0.15,
        2,
    )

    final_score = round(
        evidence_score * 0.90
        + quantum * 0.10,
        2,
    )

    if candidate_type == "direct":
        final_score = min(final_score, 55.0)

    return {
        "evidence": evidence_score,
        "clinical": round(clinical, 2),
        "literature": round(literature, 2),
        "mechanistic": round(mechanistic, 2),
        "independence": round(independence, 2),
        "quantum": round(quantum, 2),
        "final": round(final_score, 2),
    }