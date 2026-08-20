from fastapi.testclient import TestClient

from backend.api import routes
from backend.main import app

class QuestionnaireResponse:
    text = 'Here is the questionnaire:\n```json\n{"questions": [{"question_id": "q_001", "question_text": "Which additional symptom is present?", "answer_type": "multiple_choice", "options": ["Headache", "No additional symptoms"], "purpose": "symptom follow-up"}]}\n```'


def questionnaire_generator(*, contents: str, config=None):
    if "Generate 8 concise" in contents:
        return QuestionnaireResponse(), "test-model"
    raise RuntimeError("LLM explanation intentionally unavailable in this test")


routes.configure_llm(questionnaire_generator)
client = TestClient(app)


def test_zero_mapped_symptoms_returns_guidance() -> None:
    response = client.post(
        "/api/generate-questionnaire",
        json={
            "patient_name": "Test",
            "age": 30,
            "gender": "other",
            "medical_history": "",
            "selected_symptoms": [],
            "symptom_description": "an unsupported made up complaint",
        },
    )
    assert response.status_code == 422
    assert "suggested_supported_symptoms" in response.json()["detail"]


def test_end_to_end_pass1_questions_pass2() -> None:
    request = {
        "patient_name": "Test",
        "age": 30,
        "gender": "female",
        "medical_history": "asthma",
        "selected_symptoms": ["high_fever", "chills"],
        "symptom_description": "high fever with chills and sweating",
    }
    questionnaire_response = client.post("/api/generate-questionnaire", json=request)
    assert questionnaire_response.status_code == 200
    body = questionnaire_response.json()
    assert body["questions"]
    assert body["questions"]
    assert body["questionnaire_method"] == "llm_generated_multiple_choice"
    assert body["llm_selected_symptoms"] is True

    answers = {}
    for question in body["questions"]:
        answers[question["question_id"]] = "Headache"
    analyze_response = client.post(
        "/api/analyze",
        json={
            **request,
            "questionnaire": body["questions"],
            "questionnaire_answers": answers,
            "lab_report_text": None,
        },
    )
    assert analyze_response.status_code == 200
    result = analyze_response.json()
    assert result["pass1_predictions"]
    assert result["pass2_predictions"]
    assert result["patient_context"]["used_by_disease_classifier"] is False
    assert result["labs"]["used_by_disease_classifier"] is False
    assert result["evidence"]["unchecked_options_remain"] == "unknown"
    assert result["condition_definition"]
    assert result["precautionary_countermeasures"]
    assert all("name" in item for item in result["differential_diagnoses"])
    comparison = result["three_way_comparison"]
    assert comparison["ml_only"]["information_scope"] == "initial_information_only"
    assert comparison["hybrid_ml_llm"]["additional_information"]
    assert comparison["llm_only"]["source"] == "llm_unavailable_abstention"
    assert comparison["agreement"]["status"] in {
        "complete_agreement", "partial_agreement", "disagreement"
    }
    assert result["medical_disclaimer"]
