from __future__ import annotations

from typing import Dict, Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


MODEL_NAME = "wesin/pubmedbert-relation-extraction"


class AIRelationExtractor:

    def __init__(self):

        print("Loading biomedical AI model...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )

        self.model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME
        )

        self.model.eval()

        self.id2label = self.model.config.id2label

        print("Biomedical AI model loaded.")

    def _prepare_sentence(
        self,
        sentence: str,
        entity1: str,
        entity2: str,
    ) -> str:

        sentence = sentence.replace(
            entity1,
            f"[E1]{entity1}[/E1]",
            1,
        )

        sentence = sentence.replace(
            entity2,
            f"[E2]{entity2}[/E2]",
            1,
        )

        return sentence

    def predict_relation(
        self,
        sentence: str,
        entity1: str,
        entity2: str,
    ) -> Dict:

        prepared = self._prepare_sentence(
            sentence,
            entity1,
            entity2,
        )

        inputs = self.tokenizer(
            prepared,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        with torch.no_grad():

            outputs = self.model(
                **inputs
            )

        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )[0]

        confidence, index = torch.max(
            probabilities,
            dim=0,
        )

        label = self.id2label[
            int(index)
        ]

        return {
            "entity1": entity1,
            "entity2": entity2,
            "relation": label,
            "confidence": round(
                float(confidence),
                4,
            ),
            "model": MODEL_NAME,
        }


_ai_model: Optional[AIRelationExtractor] = None


def get_ai_model():

    global _ai_model

    if _ai_model is None:

        _ai_model = AIRelationExtractor()

    return _ai_model


def analyze_relationship(
    sentence: str,
    entity1: str,
    entity2: str,
) -> Dict:

    model = get_ai_model()

    return model.predict_relation(
        sentence=sentence,
        entity1=entity1,
        entity2=entity2,
    )


if __name__ == "__main__":

    sentence = (
        "Siponimod modulates the S1P receptor "
        "and may influence neuroinflammatory "
        "pathways involved in Alzheimer's disease."
    )

    result = analyze_relationship(
        sentence=sentence,
        entity1="Siponimod",
        entity2="S1P receptor",
    )

    print("\nAI RELATIONSHIP RESULT")
    print("=" * 50)

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )   