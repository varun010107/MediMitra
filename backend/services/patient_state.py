"""Present/absent/unknown/asked symptom evidence state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PatientState:
    patient_context: dict[str, Any]
    initial_text: str = ""
    present_symptoms: set[str] = field(default_factory=set)
    absent_symptoms: set[str] = field(default_factory=set)
    unknown_symptoms: set[str] = field(default_factory=set)
    asked_symptoms: set[str] = field(default_factory=set)
    pass1_predictions: list[dict[str, Any]] = field(default_factory=list)
    pass2_predictions: list[dict[str, Any]] = field(default_factory=list)

    def apply_question_answer(self, question: dict[str, Any], selected_values: list[str]) -> None:
        """Apply checkbox semantics; unchecked options remain unknown."""
        options = question.get("options", [])
        displayed = {
            option["symptom_id"] for option in options if option.get("symptom_id")
        }
        valid_values = displayed | {"none"}
        selected = set(selected_values)
        if not selected or not selected.issubset(valid_values):
            raise ValueError("Question answer contains an unsupported option")
        self.asked_symptoms.update(displayed)
        self.unknown_symptoms.update(displayed)
        if "none" in selected:
            if len(selected) != 1:
                raise ValueError("None of the above is mutually exclusive")
            self.absent_symptoms.update(displayed)
            self.present_symptoms.difference_update(displayed)
            self.unknown_symptoms.difference_update(displayed)
            return
        self.present_symptoms.update(selected)
        self.absent_symptoms.difference_update(selected)
        self.unknown_symptoms.difference_update(selected)
        # Intentionally do not mark unselected checkbox options absent.

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("present_symptoms", "absent_symptoms", "unknown_symptoms", "asked_symptoms"):
            payload[key] = sorted(payload[key])
        return payload
