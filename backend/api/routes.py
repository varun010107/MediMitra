"""Existing MediMitra workflow extended with dataset-constrained ML services."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.llm_service import LLMService
from backend.services.disease_info_service import DiseaseInfoService
from backend.services.comparison_service import agreement_analysis, prediction_summary
from backend.services.patient_state import PatientState
from backend.services.prediction_service import NoMappedSymptomsError, PredictionService
from backend.services.question_selector import QuestionSelector
from backend.services.risk_engine import RiskEngine
from backend.services.symptom_mapper import SymptomMapper

LOGGER = logging.getLogger(__name__)
BACKEND = Path(__file__).resolve().parents[1]
QUESTIONNAIRE_MAX_QUESTIONS = 8
router = APIRouter(prefix="/api")
_llm_service = LLMService()


def configure_llm(generator: Callable[..., tuple[Any, str]] | None) -> None:
    global _llm_service
    _llm_service = LLMService(generator)


@lru_cache(maxsize=1)
def prediction_service() -> PredictionService:
    return PredictionService()


@lru_cache(maxsize=1)
def symptom_mapper() -> SymptomMapper:
    return SymptomMapper(BACKEND / "data" / "symptom_vocabulary.json")


@lru_cache(maxsize=1)
def question_selector() -> QuestionSelector:
    return QuestionSelector(
        BACKEND / "data" / "symptom_vocabulary.json",
        BACKEND / "data" / "disease_symptom_stats.json",
    )


@lru_cache(maxsize=1)
def risk_engine() -> RiskEngine:
    return RiskEngine(BACKEND / "data" / "risk_rules.json")


@lru_cache(maxsize=1)
def disease_info_service() -> DiseaseInfoService:
    return DiseaseInfoService(BACKEND / "data")


class NormalizeSymptomsRequest(BaseModel):
    text: str = ""
    selected_symptoms: list[str] = Field(default_factory=list)


class QuestionnaireRequest(BaseModel):
    patient_name: str
    age: int = Field(ge=0, le=120)
    gender: str
    medical_history: str = ""
    selected_symptoms: list[str] = Field(default_factory=list)
    symptom_description: str = ""


class DiagnosisRequest(QuestionnaireRequest):
    questionnaire_answers: dict[str, Any] = Field(default_factory=dict)
    questionnaire: list[dict[str, Any]] = Field(default_factory=list)
    lab_report_text: str | None = None


def _map_or_422(text: str, selections: list[str]) -> dict[str, Any]:
    mapping = symptom_mapper().map_text(text, selections)
    if not mapping["present_symptoms"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No supported symptoms could be mapped. Describe symptoms differently or select a supported symptom.",
                "unmapped_phrases": mapping["unmapped_phrases"],
                "suggested_supported_symptoms": list(symptom_mapper().vocabulary[:12]),
            },
        )
    return mapping


@router.get("/symptoms")
def get_symptoms() -> dict[str, Any]:
    mapper = symptom_mapper()
    return {
        "symptoms": list(mapper.vocabulary),
        "display_names": {item: item.replace("_", " ").capitalize() for item in mapper.vocabulary},
    }


@router.post("/normalize-symptoms")
def normalize_symptoms(request: NormalizeSymptomsRequest) -> dict[str, Any]:
    return symptom_mapper().map_text(request.text, request.selected_symptoms)


@router.post("/generate-questionnaire")
def generate_questionnaire(request: QuestionnaireRequest) -> dict[str, Any]:
    mapping = _map_or_422(request.symptom_description, request.selected_symptoms)
    try:
        pass1 = prediction_service().predict_initial(mapping["present_symptoms"])
    except NoMappedSymptomsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    state = PatientState(
        patient_context={
            "name": request.patient_name,
            "age": request.age,
            "gender": request.gender,
            "medical_history": request.medical_history,
            "used_by_disease_classifier": False,
        },
        initial_text=request.symptom_description,
        present_symptoms=set(mapping["present_symptoms"]),
        absent_symptoms=set(mapping["absent_symptoms"]),
        pass1_predictions=pass1["predictions"],
    )
    initial_case = {
        "age": request.age,
        "gender": request.gender,
        "medical_history": request.medical_history,
        "structured_symptoms": sorted(state.present_symptoms),
        "free_text_symptom_description": request.symptom_description,
    }
    try:
        questionnaire_result = _llm_service.generate_questionnaire(
            initial_case, pass1["predictions"], QUESTIONNAIRE_MAX_QUESTIONS
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM questionnaire generation failed: {exc}") from exc
    return {
        "questions": questionnaire_result["questions"],
        "symptom_mapping": mapping,
        "pass1_prediction": pass1,
        "patient_state": state.to_dict(),
        "questionnaire_method": "llm_generated_multiple_choice",
        "llm_selected_symptoms": True,
        "questionnaire_llm": {"source": questionnaire_result["source"], "model": questionnaire_result["model"]},
    }


@router.post("/analyze")
def analyze_patient(request: DiagnosisRequest) -> dict[str, Any]:
    mapping = _map_or_422(request.symptom_description, request.selected_symptoms)
    initial_present = set(mapping["present_symptoms"])
    initial_case = {
        "age": request.age,
        "gender": request.gender,
        "medical_history": request.medical_history,
        "structured_symptoms": sorted(initial_present),
        "free_text_symptom_description": request.symptom_description,
        "medical_record_information": request.lab_report_text,
    }
    # Intentionally runs before ML and receives no ML-derived information.
    llm_only = _llm_service.independent_assessment(initial_case)
    pass1 = prediction_service().predict_initial(initial_present)
    initial_risk = risk_engine().assess(
        initial_present,
        patient_context={"age": request.age, "gender": request.gender},
        labs={"unstructured_summary": request.lab_report_text} if request.lab_report_text else {},
    )
    state = PatientState(
        patient_context={
            "name": request.patient_name,
            "age": request.age,
            "gender": request.gender,
            "medical_history": request.medical_history,
            "used_by_disease_classifier": False,
        },
        initial_text=request.symptom_description,
        present_symptoms=set(initial_present),
        absent_symptoms=set(mapping["absent_symptoms"]),
        pass1_predictions=pass1["predictions"],
    )
    questionnaire_text_answers: list[dict[str, Any]] = []
    for question in request.questionnaire:
        question_id = str(question.get("question_id", ""))
        answer = request.questionnaire_answers.get(question_id)
        if answer is None or not str(answer).strip():
            raise HTTPException(status_code=422, detail=f"Missing answer for {question_id}")
        options = [str(item) for item in question.get("options", [])]
        if str(answer) not in options:
            raise HTTPException(status_code=422, detail=f"Invalid answer for {question_id}")
        questionnaire_text_answers.append({
            "question": str(question.get("question_text", "")).strip(),
            "answer": str(answer).strip(),
        })
    answer_text = " ".join(
        item["answer"] for item in questionnaire_text_answers
        if item["answer"].casefold() != "none of the above"
    )
    answer_mapping = symptom_mapper().map_text(answer_text)
    state.present_symptoms.update(answer_mapping["present_symptoms"])
    state.absent_symptoms.update(answer_mapping["absent_symptoms"])
    questionnaire_positive = sorted(state.present_symptoms - initial_present)
    pass2 = prediction_service().predict_final(initial_present, questionnaire_positive)
    state.pass2_predictions = pass2["predictions"]
    risk = risk_engine().assess(
        state.present_symptoms,
        patient_context=state.patient_context,
        labs={"unstructured_summary": request.lab_report_text} if request.lab_report_text else {},
    )
    top = pass2["predictions"][0]
    alternatives = pass2["predictions"][1:]
    disease_info = disease_info_service().get(top["disease"])
    structured = {
        "most_likely_condition": {
            "name": top["disease"],
            "model_confidence": top["model_confidence"],
        },
        "alternative_conditions": [
            {"name": item["disease"], "model_confidence": item["model_confidence"]}
            for item in alternatives
        ],
        "pass1_predictions": pass1["predictions"],
        "pass2_predictions": pass2["predictions"],
        "patient_context": state.patient_context,
        "evidence": {
            "initial_symptoms": sorted(initial_present),
            "questionnaire_positive": questionnaire_positive,
            "questionnaire_negative": sorted(state.absent_symptoms - set(mapping["absent_symptoms"])),
            "questionnaire_unknown": sorted(state.unknown_symptoms),
            "questionnaire_text_answers": questionnaire_text_answers,
            "questionnaire_answer_symptom_mapping": answer_mapping,
            "initial_explicit_negative": sorted(mapping["absent_symptoms"]),
            "asked_symptoms": sorted(state.asked_symptoms),
            "unchecked_options_remain": "unknown",
        },
        "llm_questionnaire_context": {
            "questions": request.questionnaire,
            "answers": questionnaire_text_answers,
            "answer_symptom_mapping": answer_mapping,
            "note": "LLM receives the complete questionnaire text and answers; ML uses only mapped supported symptoms.",
        },
        "risk_assessment": risk,
        "condition_information": disease_info,
        "labs": {
            "summary": request.lab_report_text,
            "used_by_disease_classifier": False,
        },
        "model": {
            "name": pass2["model_name"],
            "version": pass2["model_version"],
            "features": "dataset-supported present symptoms only",
        },
        "confidence_notice": pass2["confidence_notice"],
        "medical_disclaimer": "Educational/research prototype only. This output is not a diagnosis or clinical validation.",
    }
    explanation = _llm_service.explain(structured)
    structured["llm_report"] = explanation

    ml_only = {
        "predictions": pass1["predictions"],
        "summary": prediction_summary(pass1["predictions"]),
        "severity": initial_risk["level"],
        "important_features": sorted(initial_present),
        "information_scope": "initial_information_only",
    }
    hybrid = {
        "initial_predictions": pass1["predictions"],
        "questions_asked": request.questionnaire,
        "additional_information": questionnaire_positive,
        "final_predictions": pass2["predictions"],
        "summary": prediction_summary(pass2["predictions"]),
        "severity": risk["level"],
        "confidence_change_percentage_points": round(
            (pass2["predictions"][0]["model_confidence"] - pass1["predictions"][0]["model_confidence"]) * 100,
            2,
        ),
        "information_scope": "initial_information_plus_questionnaire_information",
    }
    structured["three_way_comparison"] = {
        "initial_information": initial_case,
        "llm_only": llm_only,
        "ml_only": ml_only,
        "hybrid_ml_llm": hybrid,
        "agreement": agreement_analysis(llm_only, ml_only, hybrid),
        "research_export_schema_version": "1.0",
    }

    # Compatibility fields for the existing result/PDF components.
    structured.update({
        "primary_pathology": top["disease"],
        "model_confidence": top["model_confidence"],
        "confidence_level": "MODEL",
        "triage_level": risk["level"],
        "is_emergency": risk["level"] == "CRITICAL",
        "emergency_instructions": risk["message"] if risk["level"] in {"CRITICAL", "HIGH"} else "",
        "clinical_reasoning_summary": explanation["text"],
        "condition_definition": disease_info["definition"],
        "differential_diagnoses": structured["alternative_conditions"],
        "suggested_clinical_path": "Qualified healthcare professional assessment",
        "precautionary_countermeasures": disease_info["precautions"],
        "precaution_notice": disease_info["notice"],
    })
    LOGGER.info("PASS 1: %s", pass1["predictions"])
    LOGGER.info("UPDATED PRESENT: %s", sorted(state.present_symptoms))
    LOGGER.info("PASS 2: %s", pass2["predictions"])
    return structured
