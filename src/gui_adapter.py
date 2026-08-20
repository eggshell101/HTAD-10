def candidate_to_gui(candidate, scores=None, supporting=None):
    """
    Convert an EvidenceGraph candidate into the JSON structure
    expected by the HTAD-10 Streamlit GUI.

    This adapter preserves:
        - evidence
        - classical scores
        - AI information
        - quantum validation
        - explanation
        - supporting evidence
    """

    drug = candidate.get("drug", "Unknown")
    target = candidate.get("target", "Unknown")
    disease = candidate.get(
        "disease",
        candidate.get("candidate_disease", "Unknown"),
    )

    # ========================================================
    # EVIDENCE
    # ========================================================

    evidence_items = []

    for item in candidate.get(
        "drug_target_evidence",
        [],
    ):

        evidence_items.append(
            {
                "source": getattr(
                    item,
                    "source",
                    "Unknown",
                ),
                "title": getattr(
                    item,
                    "title",
                    "",
                ),
                "identifier": getattr(
                    item,
                    "identifier",
                    None,
                ),
                "date": getattr(
                    item,
                    "date",
                    None,
                ),
                "abstract": getattr(
                    item,
                    "abstract",
                    "",
                ),
                "url": getattr(
                    item,
                    "url",
                    None,
                ),
                "relationship": "drug_target",
            }
        )

    for item in candidate.get(
        "target_disease_evidence",
        [],
    ):

        evidence_items.append(
            {
                "source": getattr(
                    item,
                    "source",
                    "Unknown",
                ),
                "title": getattr(
                    item,
                    "title",
                    "",
                ),
                "identifier": getattr(
                    item,
                    "identifier",
                    None,
                ),
                "date": getattr(
                    item,
                    "date",
                    None,
                ),
                "abstract": getattr(
                    item,
                    "abstract",
                    "",
                ),
                "url": getattr(
                    item,
                    "url",
                    None,
                ),
                "relationship": "target_disease",
            }
        )

    for item in candidate.get(
        "drug_disease_evidence",
        [],
    ):

        evidence_items.append(
            {
                "source": getattr(
                    item,
                    "source",
                    "Unknown",
                ),
                "title": getattr(
                    item,
                    "title",
                    "",
                ),
                "identifier": getattr(
                    item,
                    "identifier",
                    None,
                ),
                "date": getattr(
                    item,
                    "date",
                    None,
                ),
                "abstract": getattr(
                    item,
                    "abstract",
                    "",
                ),
                "url": getattr(
                    item,
                    "url",
                    None,
                ),
                "relationship": "drug_disease",
            }
        )

    # Remove duplicate evidence.
    unique = {}

    for item in evidence_items:

        key = (
            item.get("source"),
            item.get("identifier"),
            item.get("title"),
        )

        unique[key] = item

    evidence_items = list(
        unique.values()
    )

    # ========================================================
    # SCORES
    # ========================================================

    if scores is None:
        scores = {}

    if supporting is None:
        supporting = []

    evidence_score = scores.get(
        "evidence",
        candidate.get(
            "evidence_score",
            0,
        ),
    )

    clinical_score = scores.get(
        "clinical",
        candidate.get(
            "clinical_score",
            0,
        ),
    )

    literature_score = scores.get(
        "literature",
        candidate.get(
            "literature_score",
            0,
        ),
    )

    mechanistic_score = scores.get(
        "mechanistic",
        candidate.get(
            "mechanistic_score",
            0,
        ),
    )

    independence_score = scores.get(
        "independence",
        candidate.get(
            "independence_score",
            0,
        ),
    )

    quantum_score = scores.get(
        "quantum",
        candidate.get(
            "quantum_score",
            0,
        ),
    )

    final_score = scores.get(
        "final",
        candidate.get(
            "final_score",
            0,
        ),
    )

        # ========================================================
    # QUANTUM DATA
    # ========================================================

    quantum_data = candidate.get(
        "quantum_data"
    )

    if not quantum_data:

        quantum_data = {}

    else:

        quantum_data = dict(
            quantum_data
        )

    # --------------------------------------------------------
    # Core QAOA information
    # --------------------------------------------------------

    quantum_data["status"] = candidate.get(
        "quantum_status",
        quantum_data.get(
            "quantum_status",
            quantum_data.get(
                "status",
                "pending",
            ),
        ),
    )

    quantum_data["quantum_score"] = candidate.get(
        "quantum_score",
        quantum_data.get(
            "quantum_score",
            quantum_score,
        ),
    )

    quantum_data["quantum_energy"] = candidate.get(
        "quantum_energy",
        quantum_data.get(
            "quantum_energy",
        ),
    )

    quantum_data["quantum_state"] = candidate.get(
        "quantum_state",
        quantum_data.get(
            "quantum_state",
        ),
    )

    quantum_data["quantum_features"] = candidate.get(
        "quantum_features",
        quantum_data.get(
            "quantum_features",
            {},
        ),
    )

    quantum_data["quantum_method"] = candidate.get(
        "quantum_method",
        quantum_data.get(
            "quantum_method",
            "Qiskit QAOA",
        ),
    )

    # --------------------------------------------------------
    # Classical reference
    # --------------------------------------------------------

    quantum_data["classical_energy"] = candidate.get(
        "classical_energy",
        quantum_data.get(
            "classical_energy",
        ),
    )

    quantum_data["classical_state"] = candidate.get(
        "classical_state",
        quantum_data.get(
            "classical_state",
        ),
    )

    # --------------------------------------------------------
    # QAOA validation metrics
    # --------------------------------------------------------

    quantum_data["energy_gap"] = candidate.get(
        "energy_gap",
        quantum_data.get(
            "energy_gap",
        ),
    )

    quantum_data["approximation_ratio"] = candidate.get(
        "approximation_ratio",
        quantum_data.get(
            "approximation_ratio",
        ),
    )

    quantum_data["exact_match"] = candidate.get(
        "exact_match",
        quantum_data.get(
            "exact_match",
            False,
        ),
    )

    quantum_data["quantum_executed"] = candidate.get(
        "quantum_executed",
        quantum_data.get(
            "quantum_executed",
            False,
        ),
    )

    quantum_data["quantum_advantage"] = candidate.get(
        "quantum_advantage",
        quantum_data.get(
            "quantum_advantage",
            False,
        ),
    )

    quantum_data["quantum_backend"] = candidate.get(
        "quantum_backend",
        quantum_data.get(
            "quantum_backend",
        ),
    )

    quantum_data["qaoa_reps"] = candidate.get(
        "qaoa_reps",
        quantum_data.get(
            "qaoa_reps",
        ),
    )

    quantum_data["qaoa_shots"] = candidate.get(
        "qaoa_shots",
        quantum_data.get(
            "qaoa_shots",
        ),
    )

    # --------------------------------------------------------
    # Existing GUI compatibility fields
    # --------------------------------------------------------

    quantum_data["vqe_energy"] = candidate.get(
        "vqe_energy",
        quantum_data.get(
            "vqe_energy",
        ),
    )

    quantum_data["hf_energy"] = candidate.get(
        "hf_energy",
        quantum_data.get(
            "hf_energy",
        ),
    )

    quantum_data["ai_correction"] = candidate.get(
        "ai_correction",
        quantum_data.get(
            "ai_correction",
        ),
    )

    quantum_data["final_energy"] = candidate.get(
        "final_energy",
        quantum_data.get(
            "final_energy",
        ),
    )

    quantum_data["plausibility_score"] = (
        quantum_data["quantum_score"]
    )

    # ========================================================
    # AI INFORMATION
    # ========================================================

    ai_relation = candidate.get(
        "ai_relation"
    )

    ai_confidence = candidate.get(
        "ai_confidence"
    )

    ai_model = candidate.get(
        "ai_model"
    )

    supporting_sentence = candidate.get(
        "supporting_sentence"
    )

    # ========================================================
    # FINAL GUI OBJECT
    # ========================================================

    return {

        "drug": drug,

        "existing_indications": candidate.get(
            "existing_indications",
            [],
        ),

        "target": target,

        "candidate_disease": disease,

        "candidate_type": candidate.get(
            "candidate_type",
            "mechanistic",
        ),

        "scores": {

            "evidence": evidence_score,

            "clinical": clinical_score,

            "literature": literature_score,

            "mechanistic": mechanistic_score,

            "independence": independence_score,

            "quantum": quantum_score,

            "final": final_score,
        },

        "reason": candidate.get(
            "reason",
            "",
        ),

        "supporting": supporting,

        "evidence": evidence_items,

        # ====================================================
        # AI
        # ====================================================

        "ai": {

            "relation": ai_relation,

            "confidence": ai_confidence,

            "model": ai_model,

            "supporting_sentence":
                supporting_sentence,
        },

        # ====================================================
        # QUANTUM
        # ====================================================

        "quantum": quantum_data,

        # Keep the old name too for compatibility.
        "quantum_data": quantum_data,
    }