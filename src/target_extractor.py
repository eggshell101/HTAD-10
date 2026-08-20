import re
from typing import List


TARGETS = {
    "S1P receptor": [
        "s1p receptor",
        "sphingosine-1-phosphate receptor",
        "sphingosine 1-phosphate receptor",
    ],

    "JAK": [
        "jak",
        "janus kinase",
        "janus kinases",
    ],

    "PD-1": [
        "pd-1",
        "programmed cell death protein 1",
    ],

    "PD-L1": [
        "pd-l1",
        "programmed death ligand 1",
    ],

    "EGFR": [
        "egfr",
        "epidermal growth factor receptor",
    ],

    "mTOR": [
        "mtor",
        "mechanistic target of rapamycin",
    ],

    "aromatase": [
        "aromatase",
        "cyp19a1",
    ],

    "COX": [
        "cox",
        "cyclooxygenase",
    ],
}


def normalize(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


def find_targets(text: str) -> List[str]:

    text = normalize(text)

    found = []

    for target, patterns in TARGETS.items():

        for pattern in patterns:

            if re.search(
                rf"\b{re.escape(pattern)}\b",
                text
            ):
                found.append(target)
                break

    return sorted(set(found))