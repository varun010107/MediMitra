"""Persisted symptom-only disease prediction service."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np

from .symptom_mapper import canonicalize_symptom

LOGGER = logging.getLogger(__name__)
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class NoMappedSymptomsError(ValueError):
    """Raised when inference has no supported present symptom evidence."""


class PredictionService:
    """Use the same persisted encoder/model for PASS 1 and PASS 2."""

    def __init__(self, model_dir: Path | str = MODEL_DIR, data_dir: Path | str = DATA_DIR) -> None:
        model_dir = Path(model_dir)
        data_dir = Path(data_dir)
        self.model = joblib.load(model_dir / "disease_model.pkl")
        self.symptom_encoder = joblib.load(model_dir / "symptom_encoder.pkl")
        self.label_encoder = joblib.load(model_dir / "label_encoder.pkl")
        with (model_dir / "model_metadata.json").open(encoding="utf-8") as handle:
            self.metadata = json.load(handle)
        with (data_dir / "symptom_vocabulary.json").open(encoding="utf-8") as handle:
            payload = json.load(handle)
        self.vocabulary = tuple(payload["symptoms"])
        self.vocabulary_set = set(self.vocabulary)
        LOGGER.info("Loaded disease model %s", self.metadata["model_name"])

    def _validated(self, symptoms: Iterable[str]) -> tuple[list[str], list[str]]:
        normalized = list(dict.fromkeys(canonicalize_symptom(item) for item in symptoms if canonicalize_symptom(item)))
        return (
            [item for item in normalized if item in self.vocabulary_set],
            [item for item in normalized if item not in self.vocabulary_set],
        )

    def predict(self, present_symptoms: Iterable[str], top_k: int = 5) -> dict[str, Any]:
        recognized, rejected = self._validated(present_symptoms)
        if not recognized:
            raise NoMappedSymptomsError(
                "No supported symptoms could be mapped. Describe symptoms differently or select from the supported list."
            )
        vector = self.symptom_encoder.transform([recognized])
        probabilities = self.model.predict_proba(vector)[0]
        encoded_classes = np.asarray(self.model.classes_, dtype=int)
        order = np.argsort(probabilities)[::-1][: min(top_k, len(probabilities))]
        predictions = [
            {
                "disease": str(self.label_encoder.inverse_transform([encoded_classes[index]])[0]),
                "model_confidence": round(float(probabilities[index]), 8),
            }
            for index in order
        ]
        LOGGER.info("PREDICTION: %s", predictions)
        return {
            "predictions": predictions,
            "recognized_symptoms": recognized,
            "rejected_symptoms": rejected,
            "evidence_strength": "weak" if len(recognized) == 1 else "multiple_symptoms",
            "model_name": self.metadata["model_name"],
            "model_version": self.metadata["model_version"],
            "confidence_notice": "Model confidence is not clinical certainty or real-world disease probability.",
        }

    def predict_initial(self, present_symptoms: Iterable[str], top_k: int = 5) -> dict[str, Any]:
        result = self.predict(present_symptoms, top_k)
        result["stage"] = "pass_1"
        return result

    def predict_final(
        self,
        initial_present: Iterable[str],
        questionnaire_present: Iterable[str],
        top_k: int = 5,
    ) -> dict[str, Any]:
        combined = list(dict.fromkeys([
            *(canonicalize_symptom(item) for item in initial_present),
            *(canonicalize_symptom(item) for item in questionnaire_present),
        ]))
        result = self.predict(combined, top_k)
        result["stage"] = "pass_2"
        return result
