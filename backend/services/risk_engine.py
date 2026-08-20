"""Clearly labeled, configurable prototype rule-based risk assessment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class RiskEngine:
    """Apply unvalidated prototype rules independently of model confidence."""

    def __init__(self, config_path: Path | str) -> None:
        with Path(config_path).open(encoding="utf-8") as handle:
            self.config = json.load(handle)

    def assess(
        self,
        present_symptoms: Iterable[str],
        patient_context: dict[str, Any] | None = None,
        labs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del patient_context, labs  # Stored separately; no validated context/lab rules exist yet.
        present = set(present_symptoms)
        for level in ("CRITICAL", "HIGH", "MEDIUM"):
            matched = sorted(present & set(self.config["symptom_rules"].get(level, [])))
            if matched:
                return {
                    "level": level,
                    "method": "prototype_rule_based",
                    "matched_red_flags": matched,
                    "validated_for_clinical_use": False,
                    "message": self.config["messages"][level],
                }
        return {
            "level": "LOW",
            "method": "prototype_rule_based",
            "matched_red_flags": [],
            "validated_for_clinical_use": False,
            "message": self.config["messages"]["LOW"],
        }
