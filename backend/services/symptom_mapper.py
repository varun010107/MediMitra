"""Dataset-constrained symptom normalization and free-text mapping."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

LOGGER = logging.getLogger(__name__)


def canonicalize_symptom(value: object) -> str:
    """Convert raw dataset or user text into a stable internal symptom ID."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def display_symptom(symptom_id: str) -> str:
    """Create a patient-friendly label without exposing underscore IDs."""
    return canonicalize_symptom(symptom_id).replace("_", " ").capitalize()


DEFAULT_SYNONYMS: dict[str, tuple[str, ...]] = {
    "muscle_pain": (
        "body ache",
        "body aches",
        "whole body hurts",
        "muscles hurting",
        "muscle ache",
        "arm pain",
        "left arm pain",
        "right arm pain",
        "pain in left arm",
        "pain in right arm",
    ),
    "vomiting": ("throwing up", "threw up", "vomited", "being sick"),
    "fatigue": ("feeling weak", "low energy", "very tired", "tiredness", "exhausted"),
    "high_fever": ("high fever", "fever", "high temperature"),
    "breathlessness": ("shortness of breath", "difficulty breathing", "out of breath"),
    "diarrhoea": ("diarrhea", "loose stools", "watery stools"),
    "skin_rash": ("skin rash", "rash", "red rash"),
    "abdominal_pain": ("abdominal pain", "tummy pain", "belly ache"),
    "headache": ("head ache", "head pain", "head hurts"),
    "loss_of_appetite": ("no appetite", "poor appetite", "not hungry"),
    "burning_micturition": ("burning urination", "burning when urinating", "painful urination"),
    "continuous_sneezing": ("sneezing a lot", "continuous sneezing"),
}

NEGATION_PATTERN = re.compile(
    r"(?:\bno\b|\bnot\b|\bwithout\b|\bdenies\b|\bdon't have\b|\bdo not have\b)\s+(?:any\s+)?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MappingItem:
    input_phrase: str
    symptom_id: str
    confidence: float
    status: str
    method: str


class SymptomMapper:
    """Map only exact vocabulary symptoms or reviewed common synonyms."""

    def __init__(self, vocabulary_path: Path | str) -> None:
        with Path(vocabulary_path).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        values = payload["symptoms"] if isinstance(payload, dict) else payload
        self.vocabulary = tuple(sorted(canonicalize_symptom(item) for item in values))
        self.vocabulary_set = set(self.vocabulary)
        aliases: dict[str, tuple[str, float, str]] = {}
        for symptom_id in self.vocabulary:
            aliases[symptom_id.replace("_", " ")] = (symptom_id, 1.0, "normalized_exact")
        for symptom_id, phrases in DEFAULT_SYNONYMS.items():
            if symptom_id in self.vocabulary_set:
                for phrase in phrases:
                    aliases[phrase] = (symptom_id, 0.9, "reviewed_synonym")
        self.aliases = aliases

    @staticmethod
    def _is_negated(text: str, start: int) -> bool:
        prefix = text[max(0, start - 35):start]
        return bool(NEGATION_PATTERN.search(prefix))

    def validate_symptoms(self, symptoms: Iterable[str]) -> tuple[list[str], list[str]]:
        """Partition explicit inputs into supported and unsupported canonical IDs."""
        normalized = list(dict.fromkeys(canonicalize_symptom(item) for item in symptoms if canonicalize_symptom(item)))
        return (
            [item for item in normalized if item in self.vocabulary_set],
            [item for item in normalized if item not in self.vocabulary_set],
        )

    def map_text(self, text: str, explicit_symptoms: Iterable[str] = ()) -> dict[str, object]:
        """Map free text without allowing unsupported features into the model."""
        original = text or ""
        normalized_text = re.sub(r"[^a-z0-9']+", " ", original.lower()).strip()
        present, invalid_explicit = self.validate_symptoms(explicit_symptoms)
        absent: list[str] = []
        details: list[MappingItem] = [
            MappingItem(item, item, 1.0, "present", "explicit_selection") for item in present
        ]

        occupied: list[tuple[int, int]] = []
        for phrase in sorted(self.aliases, key=len, reverse=True):
            symptom_id, confidence, method = self.aliases[phrase]
            pattern = re.compile(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])")
            for match in pattern.finditer(normalized_text):
                if any(match.start() < end and match.end() > start for start, end in occupied):
                    continue
                status = "absent" if self._is_negated(normalized_text, match.start()) else "present"
                target = absent if status == "absent" else present
                other = present if status == "absent" else absent
                if symptom_id not in target and symptom_id not in other:
                    target.append(symptom_id)
                    details.append(MappingItem(phrase, symptom_id, confidence, status, method))
                occupied.append((match.start(), match.end()))

        present = list(dict.fromkeys(item for item in present if item not in absent))
        absent = list(dict.fromkeys(absent))
        result = {
            "original_text": original,
            "present_symptoms": present,
            "absent_symptoms": absent,
            "mapped_symptoms": [asdict(item) for item in details],
            "unmapped_phrases": [original] if original.strip() and not details else [],
            "invalid_explicit_symptoms": invalid_explicit,
            "supported_symptom_count": len(self.vocabulary),
        }
        LOGGER.info("INITIAL TEXT: %r", original)
        LOGGER.info("MAPPED PRESENT: %s ABSENT: %s", present, absent)
        return result
