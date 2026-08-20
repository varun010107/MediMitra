"""Dataset-driven discriminative symptom question selection."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .symptom_mapper import display_symptom

LOGGER = logging.getLogger(__name__)

RELATED_FOLLOWUPS: dict[str, tuple[str, ...]] = {
    "muscle_pain": (
        "muscle_weakness",
        "weakness_in_limbs",
        "joint_pain",
        "swelling_joints",
        "neck_pain",
        "chest_pain",
    ),
    "joint_pain": (
        "swelling_joints",
        "painful_walking",
        "muscle_weakness",
        "weakness_in_limbs",
        "neck_pain",
        "back_pain",
    ),
}


class QuestionSelector:
    """Rank unanswered symptoms by weighted variance across Top-K diseases."""

    def __init__(self, vocabulary_path: Path | str, statistics_path: Path | str) -> None:
        with Path(vocabulary_path).open(encoding="utf-8") as handle:
            vocabulary_payload = json.load(handle)
        with Path(statistics_path).open(encoding="utf-8") as handle:
            statistics_payload = json.load(handle)
        self.vocabulary = set(vocabulary_payload["symptoms"])
        self.statistics = statistics_payload["statistics"]

    def related_followups(
        self,
        present: Iterable[str] = (),
        absent: Iterable[str] = (),
        asked: Iterable[str] = (),
    ) -> list[dict[str, float | str]]:
        """Prioritize reviewed, dataset-supported follow-ups for broad pain inputs."""
        present_set = set(present)
        excluded = present_set | set(absent) | set(asked)
        selected: list[dict[str, float | str]] = []
        seen: set[str] = set()
        for reported_symptom in present_set:
            for symptom in RELATED_FOLLOWUPS.get(reported_symptom, ()):
                if symptom in self.vocabulary and symptom not in excluded and symptom not in seen:
                    selected.append({
                        "symptom_id": symptom,
                        "score": 1.0,
                        "weighted_variance": 0.0,
                        "relevance": 1.0,
                        "selection_method": "reported_symptom_followup",
                    })
                    seen.add(symptom)
        return selected

    def rank_symptoms(
        self,
        predictions: list[dict[str, Any]],
        present: Iterable[str] = (),
        absent: Iterable[str] = (),
        asked: Iterable[str] = (),
    ) -> list[dict[str, float | str]]:
        excluded = set(present) | set(absent) | set(asked)
        diseases = [item["disease"] for item in predictions if item["disease"] in self.statistics]
        weights = np.asarray([item["model_confidence"] for item in predictions if item["disease"] in self.statistics], dtype=float)
        if not diseases:
            return []
        weights = weights / weights.sum() if weights.sum() else np.full(len(weights), 1 / len(weights))
        ranked = []
        for symptom in self.vocabulary - excluded:
            values = np.asarray([self.statistics[disease].get(symptom, 0.0) for disease in diseases])
            relevance = float(values.max())
            if relevance <= 0:
                continue
            mean = float(np.sum(weights * values))
            weighted_variance = float(np.sum(weights * (values - mean) ** 2))
            score = weighted_variance * (0.5 + relevance)
            if score > 1e-8:
                ranked.append({
                    "symptom_id": symptom,
                    "score": score,
                    "weighted_variance": weighted_variance,
                    "relevance": relevance,
                })
        ranked.sort(key=lambda item: (item["score"], item["relevance"]), reverse=True)
        return ranked

    def build_questions(
        self,
        predictions: list[dict[str, Any]],
        present: Iterable[str] = (),
        absent: Iterable[str] = (),
        asked: Iterable[str] = (),
        max_questions: int = 8,
        group_size: int = 3,
    ) -> list[dict[str, Any]]:
        ranked = self.rank_symptoms(predictions, present, absent, asked)
        focused = self.related_followups(present, absent, asked)
        focused_ids = {str(item["symptom_id"]) for item in focused}
        combined = [*focused, *(item for item in ranked if str(item["symptom_id"]) not in focused_ids)]
        selected = combined[: max_questions * group_size]
        questions = []
        for question_index in range(max_questions):
            group = selected[question_index * group_size:(question_index + 1) * group_size]
            if not group:
                break
            options = [
                {"label": display_symptom(str(item["symptom_id"])), "symptom_id": item["symptom_id"]}
                for item in group
            ]
            options.append({"label": "None of the above", "value": "none"})
            is_reported_symptom_followup = any(
                item.get("selection_method") == "reported_symptom_followup" for item in group
            )
            question = {
                "question_id": f"q_{question_index + 1:03d}",
                "question_type": "multi_select",
                "question_text": (
                    "To better understand the reported muscle or arm pain, which of these are you currently experiencing?"
                    if is_reported_symptom_followup
                    else "Which of the following symptoms are you currently experiencing?"
                ),
                "options": options,
                "selection_basis": [
                    {
                        "symptom_id": item["symptom_id"],
                        "discriminative_score": round(float(item["score"]), 8),
                        "method": item.get("selection_method", "weighted_variance"),
                    }
                    for item in group
                ],
            }
            self.validate_question(question)
            questions.append(question)
        LOGGER.info("SELECTED QUESTION FEATURES: %s", [[o.get("symptom_id") for o in q["options"] if o.get("symptom_id")] for q in questions])
        return questions

    def validate_question(self, question: dict[str, Any]) -> None:
        for option in question.get("options", []):
            symptom_id = option.get("symptom_id")
            if symptom_id and symptom_id not in self.vocabulary:
                raise ValueError(f"Question contains unsupported symptom: {symptom_id}")
