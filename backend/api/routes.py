"""LLM-only patient screening endpoints. Archived ML modules are not imported."""
from __future__ import annotations

import logging
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.services.assessment_service import AssessmentService, FollowupQuestion, Questionnaire, MIN_QUESTIONS, MAX_QUESTIONS, case_evidence
from backend.services.provider_errors import ScreeningUnavailableError

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
_service = AssessmentService()


def configure_llm(generator: Callable | None) -> None:
    global _service
    _service = AssessmentService(generator)


class QuestionnaireRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    patient_name: str = Field(min_length=1, max_length=150)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=100)
    medical_history: str = Field(default="", max_length=10000)
    selected_symptoms: list[str] = Field(default_factory=list, max_length=100)
    symptom_description: str = Field(default="", max_length=10000)
    lab_report_text: str | None = Field(default=None, max_length=20000)

    @model_validator(mode="after")
    def require_symptoms(self):
        if not self.symptom_description.strip() and not any(s.strip() for s in self.selected_symptoms):
            raise ValueError("Describe your symptoms or select at least one symptom")
        if any(len(s) > 300 for s in self.selected_symptoms):
            raise ValueError("Selected symptoms are too long")
        return self

    def patient_case(self) -> dict[str, Any]:
        # Names/contact details do not help the assessment and are not sent to Gemini.
        return self.model_dump(exclude={"patient_name", "questionnaire", "questionnaire_answers", "additional_details"})


class DiagnosisRequest(QuestionnaireRequest):
    questionnaire: list[FollowupQuestion] = Field(min_length=MIN_QUESTIONS, max_length=MAX_QUESTIONS)
    questionnaire_answers: dict[str, str]
    additional_details: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_questionnaire(self):
        Questionnaire(questions=self.questionnaire)
        return self


def unavailable(exc: Exception):
    LOGGER.warning("LLM screening request failed (%s)", type(exc).__name__)
    return HTTPException(
        status_code=503,
        detail=str(exc) if isinstance(exc, ScreeningUnavailableError) else "The AI returned an incomplete or invalid response. Please try again. No assessment was produced.",
    )


@router.post("/generate-questionnaire")
def generate_questionnaire(request: QuestionnaireRequest):
    try:
        return _service.questionnaire(request.patient_case())
    except Exception as exc:
        raise unavailable(exc) from exc


@router.post("/analyze")
def analyze_patient(request: DiagnosisRequest):
    ids = [question.question_id for question in request.questionnaire]
    if len(set(ids)) != len(ids) or set(request.questionnaire_answers) != set(ids):
        raise HTTPException(status_code=422, detail="Answer every follow-up question exactly once.")
    answers = []
    for question in request.questionnaire:
        answer = request.questionnaire_answers[question.question_id]
        if answer not in question.options:
            raise HTTPException(status_code=422, detail=f"Select a valid answer for {question.question_id}.")
        answers.append({"question": question.question_text, "answer": answer})
    evidence = case_evidence(request.patient_case(), answers, request.additional_details)
    try:
        return _service.assess(evidence)
    except Exception as exc:
        raise unavailable(exc) from exc
