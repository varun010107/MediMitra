import pytest

from backend.services.llm_service import LLMService, preserve_question_options
from backend.services.disease_info_service import DiseaseInfoService
from backend.services.patient_state import PatientState


def question() -> dict:
    return {
        "question_id": "q_001",
        "question_type": "multi_select",
        "options": [
            {"label": "Chills", "symptom_id": "chills"},
            {"label": "Sweating", "symptom_id": "sweating"},
            {"label": "Skin rash", "symptom_id": "skin_rash"},
            {"label": "None of the above", "value": "none"},
        ],
    }


def test_checkbox_multiple_selection() -> None:
    state = PatientState(patient_context={})
    state.apply_question_answer(question(), ["chills", "skin_rash"])
    assert {"chills", "skin_rash"} <= state.present_symptoms


def test_none_is_mutually_exclusive() -> None:
    state = PatientState(patient_context={})
    with pytest.raises(ValueError):
        state.apply_question_answer(question(), ["none", "chills"])


def test_none_marks_all_displayed_absent() -> None:
    state = PatientState(patient_context={})
    state.apply_question_answer(question(), ["none"])
    assert state.absent_symptoms == {"chills", "sweating", "skin_rash"}


def test_unchecked_options_remain_unknown() -> None:
    state = PatientState(patient_context={})
    state.apply_question_answer(question(), ["skin_rash"])
    assert state.absent_symptoms == set()
    assert state.unknown_symptoms == {"chills", "sweating"}


def test_asked_symptoms_are_recorded() -> None:
    state = PatientState(patient_context={})
    state.apply_question_answer(question(), ["skin_rash"])
    assert state.asked_symptoms == {"chills", "sweating", "skin_rash"}


def test_llm_phrasing_cannot_change_options() -> None:
    original = question()
    phrased = preserve_question_options(original, "A friendlier question?")
    assert phrased["question_text"] == "A friendlier question?"
    assert phrased["options"] == original["options"]
    assert all(option.get("symptom_id") != "invented_feature" for option in phrased["options"])


def test_final_report_prompt_requests_safe_condition_definition() -> None:
    captured: dict[str, str] = {}

    class Response:
        text = "Condition overview: A neutral definition. Model interpretation: Test. Safety note: Not a diagnosis."

    def generator(*, contents: str, config=None):
        captured["prompt"] = contents
        return Response(), "test-model"

    result = LLMService(generator).explain(
        {
            "most_likely_condition": {
                "name": "Malaria",
                "model_confidence": 0.42,
            },
            "alternative_conditions": [],
            "evidence": {"initial_symptoms": ["high_fever"]},
            "condition_information": {
                "definition": "Malaria is an infectious disease caused by parasites.",
                "precautions": ["Consult a qualified healthcare professional."],
            },
        }
    )

    assert "Condition overview:" in captured["prompt"]
    assert "condition_information.definition" in captured["prompt"]
    assert "do not add treatment, medication" in captured["prompt"]
    assert result["source"] == "llm_explanation_only"


def test_disease_info_is_available_without_llm() -> None:
    info = DiseaseInfoService().get("Osteoarthritis")

    assert "cartilage" in info["definition"].casefold()
    assert len(info["precautions"]) >= 3
    assert not any("acetaminophen" in item.casefold() for item in info["precautions"])
    assert info["used_by_disease_classifier"] is False


def test_llm_questionnaire_is_multiple_choice_and_adds_none_option() -> None:
    class Response:
        text = '```json\n{"questions": [{"question_text": "Which is present?", "options": ["Sweating", "Chills"]}]}\n```'

    def generator(*, contents: str, config=None):
        return Response(), "test-model"

    result = LLMService(generator).generate_questionnaire({}, [], 8)

    assert result["questions"][0]["answer_type"] == "multiple_choice"
    assert result["questions"][0]["options"][-1] == "None of the above"
