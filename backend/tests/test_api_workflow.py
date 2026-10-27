"""Mocked provider tests: no API key, disease model, or classifier dependencies."""
import copy
import json
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.api import routes
from backend.main import app

CASE = {
    "patient_name": "Test Patient", "age": 35, "gender": "Female",
    "medical_history": "History detail used by the AI", "selected_symptoms": [],
    "symptom_description": "A complaint outside any fixed symptom vocabulary",
    "lab_report_text": "A reported lab finding",
}
QUESTION = {
    "question_id": "q_001", "question_text": "When did this start?",
    "options": ["Today", "Several days ago"], "purpose": "Clarify duration",
}
QUESTIONS = [{**QUESTION, 'question_id': f'q_{i:03d}', 'question_text': text} for i, text in enumerate([
    'When did this start?', 'How has it changed?', 'How much does it affect daily activities?',
    'What makes it worse?', 'What other symptoms have you noticed?', 'Has this happened before?',
], 1)]


def answers_for(questions=QUESTIONS, answer='Today'):
    return {question['question_id']: answer for question in questions}


CANDIDATE = {
    "name": "Example possibility", "overview": "An educational example.",
    "explanation": "The reported symptoms and duration may fit this possibility.",
    "evidence_ids": ["E4", "E7"], "uncertainties": ["An examination is needed."],
}
RESULT = {
    "status": "possible_condition", "certainty": "moderate",
    "summary": "One possible explanation merits professional assessment.",
    "primary_condition": CANDIDATE, "other_possibilities": [{**CANDIDATE, "name": "Another possibility"}],
    "uncertainty_explanation": "No examination has taken place.",
    "missing_information": ["Examination findings"],
    "next_steps": ["Discuss the symptoms with a healthcare professional."],
    "urgency": "prompt", "urgency_reason": "The reported history warrants timely review.",
    "warning_signs": ["Seek urgent help if symptoms become severe."],
}


@pytest.fixture
def client():
    routes.configure_llm(None)
    with TestClient(app) as test_client:
        yield test_client
    routes.configure_llm(None)


def provider(result=None, captured=None):
    def generate(*, contents, config=None):
        if captured is not None:
            captured.append(contents)
        payload = {"questions": QUESTIONS} if "Create between 6 and 12" in contents else (result or RESULT)
        return SimpleNamespace(text=json.dumps(payload)), "test-model"
    return generate


def workflow(client, result=None, captured=None):
    routes.configure_llm(provider(result, captured))
    response = client.post('/api/generate-questionnaire', json=CASE)
    assert response.status_code == 200, response.text
    questions = response.json()['questions']
    payload = {**CASE, "questionnaire": questions, "questionnaire_answers": answers_for(questions), "additional_details": "Extra patient context"}
    return client.post('/api/analyze', json=payload), payload


def test_complete_flow_uses_history_unrestricted_symptoms_labs_and_answers(client):
    captured = []
    response, _ = workflow(client, captured=captured)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['method'] == 'llm_only'
    assert body['primary_condition']['name'] == CANDIDATE['name']
    assert body['other_possibilities']
    assert 'pass1_predictions' not in body and 'model_confidence' not in body
    for prompt in captured:
        assert CASE['medical_history'] in prompt
        assert CASE['symptom_description'] in prompt
        assert CASE['lab_report_text'] in prompt
        assert CASE['patient_name'] not in prompt
    assert 'Extra patient context' in captured[-1] and 'Today' in captured[-1]
    assert not any(name in sys.modules for name in ('backend.services.prediction_service', 'sklearn', 'joblib'))


def test_unknown_choices_are_available(client):
    routes.configure_llm(provider())
    questions = client.post('/api/generate-questionnaire', json=CASE).json()['questions']
    assert 'Not sure' in questions[0]['options']
    assert 'None of these' in questions[0]['options']


@pytest.mark.parametrize('status,certainty', [('insufficient_evidence', 'moderate'), ('insufficient_evidence', 'low')])
def test_uncertain_output_cannot_name_a_main_disease(client, status, certainty):
    result = {**RESULT, "status": status, "certainty": certainty, "urgency": "emergency"}
    response, _ = workflow(client, result)
    body = response.json()
    assert response.status_code == 200
    assert body['status'] == 'insufficient_evidence'
    assert body['primary_condition'] is None
    assert body['other_possibilities'] == []
    assert body['urgency'] == 'emergency'  # urgency survives diagnostic abstention


@pytest.mark.parametrize('answers', [{}, {'q_001': 'not a listed choice'}, {'q_001': 'Today', 'extra': 'Today'}])
def test_missing_invalid_extra_answers_rejected(client, answers):
    supplied = {} if not answers else {**answers_for(), **answers}
    response = client.post('/api/analyze', json={**CASE, 'questionnaire': QUESTIONS, 'questionnaire_answers': supplied})
    assert response.status_code == 422


def test_empty_intake_rejected_but_unrecognized_text_allowed(client):
    response = client.post('/api/generate-questionnaire', json={**CASE, 'symptom_description': ' ', 'selected_symptoms': []})
    assert response.status_code == 422
    routes.configure_llm(provider())
    assert client.post('/api/generate-questionnaire', json=CASE).status_code == 200


def test_unavailable_provider_is_service_error_not_insufficient_evidence(client):
    response = client.post('/api/generate-questionnaire', json=CASE)
    assert response.status_code == 503
    assert 'No assessment was produced' in response.json()['detail']


@pytest.mark.parametrize('output', ['not json', '{"questions": []}', '{"questions": [{"question_id": "x", "question_text": "q", "options": ["x", "x"], "purpose": "p"}]}'])
def test_malformed_questionnaire_is_retryable_error(client, output):
    routes.configure_llm(lambda **kwargs: (SimpleNamespace(text=output), 'test'))
    assert client.post('/api/generate-questionnaire', json=CASE).status_code == 503


def test_invented_evidence_rejected(client):
    result = copy.deepcopy(RESULT)
    result['primary_condition']['evidence_ids'] = ['E999']
    response, _ = workflow(client, result)
    assert response.status_code == 503


def test_report_download_for_possible_and_insufficient_results(client):
    for status in ('possible_condition', 'insufficient_evidence'):
        response, _ = workflow(client, {**RESULT, 'status': status})
        result = response.json()
        pdf = client.post('/api/generate-pdf', json={**{key: CASE[key] for key in ('patient_name', 'age', 'gender', 'medical_history')}, 'results': result})
        assert pdf.status_code == 200, pdf.text
        assert pdf.content.startswith(b'%PDF-')
        assert pdf.headers['content-type'] == 'application/pdf'
        assert pdf.headers['cache-control'] == 'no-store'


def test_pdf_rejects_unknown_evidence(client):
    response, _ = workflow(client)
    body = response.json()
    body['primary_condition']['evidence_ids'] = ['E999']
    assert client.post('/api/generate-pdf', json={**CASE, 'results': body}).status_code == 422


def test_malformed_final_output_is_not_shown_as_diagnosis(client):
    response, _ = workflow(client, {**RESULT, 'certainty': 'absolutely sure'})
    assert response.status_code == 503


def test_analysis_without_provider_returns_service_error(client):
    response = client.post('/api/analyze', json={**CASE, 'questionnaire': QUESTIONS, 'questionnaire_answers': answers_for()})
    assert response.status_code == 503
    assert 'No assessment was produced' in response.json()['detail']


def test_unknown_answers_are_preserved_as_unknown_information(client):
    routes.configure_llm(provider({**RESULT, 'status': 'insufficient_evidence', 'certainty': 'low'}))
    questions = client.post('/api/generate-questionnaire', json=CASE).json()['questions']
    response = client.post('/api/analyze', json={**CASE, 'questionnaire': questions, 'questionnaire_answers': answers_for(questions, 'Not sure')})
    assert response.status_code == 200
    assert response.json()['status'] == 'insufficient_evidence'
    assert response.json()['evidence'][-1]['text'] == 'Not sure'


def test_tentative_low_certainty_possibilities_are_not_erased(client):
    response, _ = workflow(client, {**RESULT, 'certainty': 'low'})
    assert response.status_code == 200
    result = response.json()
    assert result['status'] == 'possible_condition'
    assert result['certainty'] == 'low'
    assert result['primary_condition']['name'] == CANDIDATE['name']
    assert result['primary_condition']['uncertainties']
    assert result['other_possibilities']
    # PDF revalidation must preserve the same tentative assessment.
    pdf = client.post('/api/generate-pdf', json={**CASE, 'results': result})
    assert pdf.status_code == 200


def test_low_certainty_without_a_supported_primary_is_invalid(client):
    response, _ = workflow(client, {**RESULT, 'certainty': 'low', 'primary_condition': None})
    assert response.status_code == 503


@pytest.mark.parametrize('field', ['patient_name', 'gender'])
def test_blank_required_intake_fields_are_rejected(client, field):
    assert client.post('/api/generate-questionnaire', json={**CASE, field: '   '}).status_code == 422


@pytest.mark.parametrize('field', ['next_steps', 'warning_signs', 'missing_information'])
def test_empty_explanation_list_items_are_rejected(client, field):
    response, _ = workflow(client, {**RESULT, field: ['   ']})
    assert response.status_code == 503


def test_lab_provider_error_remains_actionable(client, monkeypatch):
    from backend import main
    from backend.services.provider_errors import ScreeningUnavailableError
    monkeypatch.setattr(main, 'client', object())
    def unavailable(*args, **kwargs):
        raise ScreeningUnavailableError('Gemini quota reached. No assessment was produced.')
    monkeypatch.setattr(main, 'generate_with_fallback', unavailable)
    response = client.post('/api/parse-lab-report', files={'file': ('test.pdf', b'%PDF-test', 'application/pdf')})
    assert response.status_code == 503
    assert 'quota' in response.json()['detail']


def test_long_lab_extraction_is_rejected_before_next_step(client, monkeypatch):
    from backend import main
    monkeypatch.setattr(main, 'client', object())
    monkeypatch.setattr(main, 'generate_with_fallback', lambda *args, **kwargs: (SimpleNamespace(text='x' * 20001), 'test'))
    response = client.post('/api/parse-lab-report', files={'file': ('test.pdf', b'%PDF-test', 'application/pdf')})
    assert response.status_code == 422
    assert 'fewer pages' in response.json()['detail']


def test_lab_findings_can_be_used_in_next_screening_step(client, monkeypatch):
    from backend import main
    monkeypatch.setattr(main, 'client', object())
    monkeypatch.setattr(main, 'generate_with_fallback', lambda *args, **kwargs: (SimpleNamespace(text='Synthetic lab context'), 'test'))
    response = client.post('/api/parse-lab-report', files={'file': ('test.pdf', b'%PDF-test', 'application/pdf')})
    assert response.status_code == 200
    routes.configure_llm(provider())
    intake = client.post('/api/generate-questionnaire', json={**CASE, 'lab_report_text': response.json()['summary']})
    assert intake.status_code == 200


@pytest.mark.parametrize('content,mime', [(b'', 'application/pdf'), (b'text', 'text/plain'), (b'x' * (10 * 1024 * 1024 + 1), 'application/pdf')])
def test_invalid_lab_uploads_are_rejected(client, monkeypatch, content, mime):
    from backend import main
    monkeypatch.setattr(main, 'client', object())
    response = client.post('/api/parse-lab-report', files={'file': ('test.pdf', content, mime)})
    assert response.status_code == 422


@pytest.mark.parametrize('count', [6, 9, 12])
def test_questionnaire_count_can_vary_within_limits(client, count):
    questions = [{**QUESTION, 'question_id': f'q_{i:03d}', 'question_text': f'Distinct synthetic question {i}?'} for i in range(count)]
    routes.configure_llm(lambda **kwargs: (SimpleNamespace(text=json.dumps({'questions': questions})), 'test-model'))
    response = client.post('/api/generate-questionnaire', json=CASE)
    assert response.status_code == 200
    assert len(response.json()['questions']) == count


def test_short_generated_questionnaire_is_repaired_once(client):
    calls = []
    def generator(**kwargs):
        calls.append(kwargs['contents'])
        return SimpleNamespace(text=json.dumps({'questions': [QUESTION] if len(calls) == 1 else QUESTIONS})), 'test-model'
    routes.configure_llm(generator)
    response = client.post('/api/generate-questionnaire', json=CASE)
    assert response.status_code == 200
    assert len(response.json()['questions']) == 6
    assert len(calls) == 2


@pytest.mark.parametrize('questions', [[QUESTION] * 6, QUESTIONS[:5], QUESTIONS + [{**QUESTION, 'question_text': f'Extra {i}?'} for i in range(7)]])
def test_invalid_count_and_duplicate_questions_are_not_shown(client, questions):
    calls = []
    def generator(**kwargs):
        calls.append(1)
        return SimpleNamespace(text=json.dumps({'questions': questions})), 'test-model'
    routes.configure_llm(generator)
    assert client.post('/api/generate-questionnaire', json=CASE).status_code == 503
    assert len(calls) == 2


def test_analysis_cannot_bypass_minimum_questions(client):
    assert client.post('/api/analyze', json={**CASE, 'questionnaire': QUESTIONS[:5], 'questionnaire_answers': answers_for(QUESTIONS[:5])}).status_code == 422


def test_analysis_rejects_repeated_questions_even_with_distinct_ids(client):
    repeated = [{**QUESTION, 'question_id': f'q_{i:03d}'} for i in range(6)]
    response = client.post('/api/analyze', json={**CASE, 'questionnaire': repeated, 'questionnaire_answers': answers_for(repeated)})
    assert response.status_code == 422
