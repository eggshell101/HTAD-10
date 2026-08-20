import re
from typing import List

from .models import Evidence, RepurposingSignal
from .target_extractor import find_targets

DRUGS = {
    "metformin",
    "aspirin",
    "ibuprofen",
    "atorvastatin",
    "simvastatin",
    "rosuvastatin",
    "ivermectin",
    "hydroxychloroquine",
    "rapamycin",
    "sirolimus",
    "sildenafil",
    "propranolol",
    "rituximab",
    "lenalidomide",
    "thalidomide",
    "minoxidil",
    "itraconazole",
    "siponimod",
    "anastrozole",
    "letrozole",
    "exemestane",
}


DISEASES = {
    "alzheimer's disease": [
        "alzheimer",
    ],

    "hepatocellular carcinoma": [
        "hepatocellular carcinoma",
        "liver cancer",
    ],

    "esophageal cancer": [
        "esophageal cancer",
        "oesophageal cancer",
    ],

    "barrett's esophagus": [
        "barrett",
    ],

    "schizophrenia": [
        "schizophrenia",
    ],

    "prostate cancer": [
        "prostate cancer",
    ],

    "mesothelioma": [
        "mesothelioma",
    ],

    "obesity": [
        "obesity",
        "overweight",
    ],
}


REPURPOSING_PATTERNS = [
    r"\brepurpos",
    r"\breposition",
    r"\boff[- ]label",
    r"\bnew indication",
    r"\bnew therapeutic",
    r"\bpotential treatment",
    r"\bpotential therapeutic",
    r"\btherapeutic potential",
    r"\bdrug reuse",
]


def normalize(text: str) -> str:

    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


def find_drugs(text: str) -> List[str]:

    text = normalize(text)

    found = []

    for drug in DRUGS:

        pattern = rf"\b{re.escape(drug)}\b"

        if re.search(pattern, text):

            found.append(drug)

    return sorted(found)


def find_diseases(text: str) -> List[str]:

    text = normalize(text)

    found = []

    for disease, patterns in DISEASES.items():

        for pattern in patterns:

            if re.search(
                rf"\b{re.escape(pattern)}\b",
                text
            ):

                found.append(disease)
                break

    return sorted(set(found))


def find_repurposing_terms(text: str) -> List[str]:

    text = normalize(text)

    found = []

    for pattern in REPURPOSING_PATTERNS:

        if re.search(pattern, text):

            found.append(pattern)

    return found


def extract_signals(
    
    evidence: List[Evidence],
) -> List[RepurposingSignal]:

    signals = []
    

    for item in evidence:

        text = " ".join([
            item.title or "",
            item.abstract or "",
        ])

        targets = find_targets(text)
        drugs = find_drugs(text)
        diseases = find_diseases(text)
        repurposing_terms = find_repurposing_terms(text)
        # No drug → no candidate
        if not drugs:
            continue

        # No disease → don't call it a repurposing signal
        if not diseases:
            continue

        # No repurposing language → currently treat as ordinary evidence
        if not repurposing_terms:
            continue

        for drug in drugs:

            for disease in diseases:

                # Stronger score if repurposing language
                # and a drug/disease pair are both present.
                evidence_score = 0.7

                if "repurpos" in " ".join(
                    repurposing_terms
                ):
                    evidence_score = 0.9

                signals.append(
                    RepurposingSignal(
                        drug=drug,
                        disease=disease,
                        target=", ".join(targets) 
                        if targets 
                        else None,
                        evidence_score=evidence_score,
                        clinical_score=0.0,
                        quantum_score=0.0,
                        final_score=evidence_score,
                        evidence=[item],
                    )
                )

    return signals