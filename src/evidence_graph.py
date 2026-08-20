from collections import defaultdict


class EvidenceGraph:

    def __init__(self, known_indications=None):

        self.drug_to_targets = defaultdict(set)

        self.target_to_diseases = defaultdict(set)

        self.drug_to_diseases = defaultdict(set)

        # Stores complete relationship records,
        # including AI confidence and supporting evidence.
        self.evidence = defaultdict(list)

        if known_indications:

            for drug, diseases in known_indications.items():

                drug = drug.lower()

                for disease in diseases:

                    self.drug_to_diseases[
                        drug
                    ].add(
                        disease.lower()
                    )

    # ========================================================
    # DRUG → TARGET
    # ========================================================

    def add_drug_target(
        self,
        drug,
        target,
        evidence,
    ):

        if not drug or not target:
            return

        drug = drug.lower()
        target = target.lower()

        self.drug_to_targets[
            drug
        ].add(
            target
        )

        self.evidence[
            ("drug_target", drug, target)
        ].append(
            evidence
        )

    # ========================================================
    # TARGET → DISEASE
    # ========================================================

    def add_target_disease(
        self,
        target,
        disease,
        evidence,
    ):

        if not target or not disease:
            return

        target = target.lower()
        disease = disease.lower()

        self.target_to_diseases[
            target
        ].add(
            disease
        )

        self.evidence[
            ("target_disease", target, disease)
        ].append(
            evidence
        )

    # ========================================================
    # DRUG → DISEASE
    # ========================================================

    def add_drug_disease(
        self,
        drug,
        disease,
        evidence,
    ):

        if not drug or not disease:
            return

        drug = drug.lower()
        disease = disease.lower()

        self.drug_to_diseases[
            drug
        ].add(
            disease
        )

        self.evidence[
            ("drug_disease", drug, disease)
        ].append(
            evidence
        )

    # ========================================================
    # INFER NEW INDICATIONS
    # ========================================================

    def infer_new_indications(self):

        candidates = []

        for drug, targets in self.drug_to_targets.items():

            for target in targets:

                diseases = (
                    self.target_to_diseases.get(
                        target,
                        set(),
                    )
                )

                for disease in diseases:

                    # ------------------------------------------------
                    # Do not rediscover an existing indication.
                    # ------------------------------------------------

                    if disease in (
                        self.drug_to_diseases.get(
                            drug,
                            set(),
                        )
                    ):
                        continue

                    # ------------------------------------------------
                    # Retrieve both sides of the mechanistic path.
                    # ------------------------------------------------

                    drug_target_evidence = (
                        self.evidence.get(
                            (
                                "drug_target",
                                drug,
                                target,
                            ),
                            [],
                        )
                    )

                    target_disease_evidence = (
                        self.evidence.get(
                            (
                                "target_disease",
                                target,
                                disease,
                            ),
                            [],
                        )
                    )

                    if not drug_target_evidence:
                        continue

                    if not target_disease_evidence:
                        continue

                    # ------------------------------------------------
                    # Calculate evidence quality.
                    # ------------------------------------------------

                    drug_target_confidences = [
                        float(
                            item.get(
                                "ai_confidence",
                                0.0,
                            )
                        )
                        for item in drug_target_evidence
                        if isinstance(item, dict)
                    ]

                    target_disease_confidences = [
                        float(
                            item.get(
                                "ai_confidence",
                                0.0,
                            )
                        )
                        for item in target_disease_evidence
                        if isinstance(item, dict)
                    ]

                    dt_confidence = (
                        max(
                            drug_target_confidences
                        )
                        if drug_target_confidences
                        else 0.0
                    )

                    td_confidence = (
                        max(
                            target_disease_confidences
                        )
                        if target_disease_confidences
                        else 0.0
                    )

                    # ------------------------------------------------
                    # Combined evidence confidence.
                    #
                    # Geometric mean prevents one extremely strong
                    # edge from completely hiding a weak edge.
                    # ------------------------------------------------

                    if (
                        dt_confidence > 0
                        and td_confidence > 0
                    ):

                        combined_confidence = (
                            dt_confidence
                            * td_confidence
                        ) ** 0.5

                    else:

                        combined_confidence = 0.0

                    # ------------------------------------------------
                    # Require meaningful AI confidence.
                    # ------------------------------------------------

                    if combined_confidence < 0.70:
                        continue

                    # ------------------------------------------------
                    # Construct candidate.
                    # ------------------------------------------------

                    candidate = {

                        "drug": drug,

                        "existing_indications": sorted(
                            self.drug_to_diseases.get(
                                drug,
                                set(),
                            )
                        ),

                        "target": target,

                        "disease": disease,

                        "reason": (
                            f"{drug} → {target} → {disease}"
                        ),

                        "relationship": (
                            "drug_target_to_target_disease"
                        ),

                        "drug_target_relation": (
                            self._best_relation(
                                drug_target_evidence
                            )
                        ),

                        "target_disease_relation": (
                            self._best_relation(
                                target_disease_evidence
                            )
                        ),

                        "drug_target_confidence": (
                            dt_confidence
                        ),

                        "target_disease_confidence": (
                            td_confidence
                        ),

                        "combined_confidence": (
                            combined_confidence
                        ),

                        "drug_target_evidence": (
                            drug_target_evidence
                        ),

                        "target_disease_evidence": (
                            target_disease_evidence
                        ),
                    }

                    candidates.append(
                        candidate
                    )

        return candidates

    # ========================================================
    # BEST AI RELATION
    # ========================================================

    @staticmethod
    def _best_relation(
        evidence_records,
    ):

        best_relation = None

        best_confidence = -1.0

        for item in evidence_records:

            if not isinstance(
                item,
                dict,
            ):
                continue

            confidence = float(
                item.get(
                    "ai_confidence",
                    0.0,
                )
            )

            if confidence > best_confidence:

                best_confidence = confidence

                best_relation = item.get(
                    "ai_relation"
                )

        return best_relation