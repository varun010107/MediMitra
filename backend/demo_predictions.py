"""Print reproducible PASS-1/PASS-2 examples using persisted artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from backend.services.prediction_service import PredictionService
from backend.services.question_selector import QuestionSelector


def main() -> None:
    backend = Path(__file__).resolve().parent
    predictor = PredictionService()
    selector = QuestionSelector(
        backend / "data" / "symptom_vocabulary.json",
        backend / "data" / "disease_symptom_stats.json",
    )
    cases = [
        ["itching", "skin_rash"],
        ["high_fever", "chills", "sweating"],
        ["acidity", "stomach_pain", "vomiting"],
    ]
    for initial in cases:
        pass1 = predictor.predict_initial(initial)
        questions = selector.build_questions(
            pass1["predictions"],
            present=set(initial),
            absent=set(),
            asked=set(),
            max_questions=1,
            group_size=3,
        )
        discovered = (
            [questions[0]["options"][0]["symptom_id"]] if questions else []
        )
        pass2 = predictor.predict_final(initial, discovered)
        print(
            json.dumps(
                {
                    "initial_symptoms": initial,
                    "pass1_top_3": pass1["predictions"][:3],
                    "questionnaire_positive": discovered,
                    "pass2_top_3": pass2["predictions"][:3],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
