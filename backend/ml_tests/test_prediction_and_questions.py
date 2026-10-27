from pathlib import Path

import pytest

from backend.services.prediction_service import NoMappedSymptomsError, PredictionService
from backend.services.question_selector import QuestionSelector

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def predictor() -> PredictionService:
    return PredictionService()


@pytest.fixture(scope="module")
def selector() -> QuestionSelector:
    return QuestionSelector(
        BACKEND / "data" / "symptom_vocabulary.json",
        BACKEND / "data" / "disease_symptom_stats.json",
    )


def test_pass1_probabilities_and_sorting(predictor: PredictionService) -> None:
    result = predictor.predict_initial(["high_fever", "chills", "sweating"])
    values = [item["model_confidence"] for item in result["predictions"]]
    assert values == sorted(values, reverse=True)
    assert all(0 <= value <= 1 for value in values)
    assert result["stage"] == "pass_1"


def test_no_symptoms_does_not_run_model(predictor: PredictionService) -> None:
    with pytest.raises(NoMappedSymptomsError):
        predictor.predict_initial(["unsupported"])


def test_pass2_uses_questionnaire_positive(predictor: PredictionService) -> None:
    initial = predictor.predict_initial(["itching"])
    final = predictor.predict_final(["itching"], ["skin_rash", "nodal_skin_eruptions"])
    assert final["stage"] == "pass_2"
    assert final["recognized_symptoms"] == ["itching", "skin_rash", "nodal_skin_eruptions"]
    assert initial["recognized_symptoms"] != final["recognized_symptoms"]


def test_patient_context_cannot_enter_classifier(predictor: PredictionService) -> None:
    with pytest.raises(TypeError):
        predictor.predict(["itching"], patient_context={"age": 50})  # type: ignore[call-arg]


def test_question_selector_returns_only_vocabulary(
    predictor: PredictionService, selector: QuestionSelector
) -> None:
    prediction = predictor.predict_initial(["high_fever", "chills"])
    questions = selector.build_questions(prediction["predictions"])
    assert questions
    for question in questions:
        for option in question["options"]:
            if option.get("symptom_id"):
                assert option["symptom_id"] in selector.vocabulary


def test_present_absent_and_asked_are_not_selected(
    predictor: PredictionService, selector: QuestionSelector
) -> None:
    prediction = predictor.predict_initial(["high_fever", "chills"])
    excluded = {"high_fever", "chills", "vomiting", "sweating"}
    ranked = selector.rank_symptoms(
        prediction["predictions"],
        present={"high_fever", "chills"},
        absent={"vomiting"},
        asked={"sweating"},
    )
    assert not excluded & {item["symptom_id"] for item in ranked}


def test_discriminative_ranking_is_descending(
    predictor: PredictionService, selector: QuestionSelector
) -> None:
    prediction = predictor.predict_initial(["high_fever"])
    ranked = selector.rank_symptoms(prediction["predictions"])
    scores = [item["score"] for item in ranked]
    assert scores == sorted(scores, reverse=True)


def test_invalid_question_symptom_is_rejected(selector: QuestionSelector) -> None:
    with pytest.raises(ValueError):
        selector.validate_question({"options": [{"symptom_id": "invented_feature"}]})


def test_muscle_pain_gets_related_dataset_supported_followups(
    predictor: PredictionService, selector: QuestionSelector
) -> None:
    prediction = predictor.predict_initial(["muscle_pain"])
    questions = selector.build_questions(
        prediction["predictions"], present={"muscle_pain"}
    )
    first_two_options = {
        option["symptom_id"]
        for question in questions[:2]
        for option in question["options"]
        if option.get("symptom_id")
    }

    assert {
        "muscle_weakness",
        "weakness_in_limbs",
        "joint_pain",
        "swelling_joints",
        "neck_pain",
        "chest_pain",
    } == first_two_options
    assert "muscle or arm pain" in questions[0]["question_text"]
