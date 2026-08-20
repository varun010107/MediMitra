"""Gemini integration for independent baseline, questions, and report wording.

The persisted ML model remains the sole disease classifier used by MediMitra.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable


LOGGER = logging.getLogger(__name__)
JSON_RESPONSE_CONFIG = {"response_mime_type": "application/json"}


def _parse_json_object(text: str) -> dict[str, Any]:
    """Extract one JSON object even if a model wraps it in Markdown prose."""
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    candidate = fenced.group(1) if fenced else cleaned
    if not candidate.startswith("{"):
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end < start:
            raise ValueError("No JSON object found in LLM response")
        candidate = candidate[start:end + 1]
    result = json.loads(candidate)
    if not isinstance(result, dict):
        raise ValueError("LLM JSON response must be an object")
    return result


def preserve_question_options(
    backend_question: dict[str, Any], proposed_text: str | None = None
) -> dict[str, Any]:
    """Allow wording changes while keeping backend-selected options immutable."""
    result = dict(backend_question)
    if proposed_text and proposed_text.strip():
        result["question_text"] = proposed_text.strip()
    result["options"] = [dict(option) for option in backend_question["options"]]
    return result


class LLMService:
    def __init__(self, generator: Callable[..., tuple[Any, str]] | None = None) -> None:
        self.generator = generator

    def explain(self, structured_result: dict[str, Any]) -> dict[str, Any]:
        """Generate prose only; structured model/risk fields remain authoritative."""
        top = structured_result["most_likely_condition"]
        condition_information = structured_result.get("condition_information", {})
        definition = condition_information.get(
            "definition",
            f"A condition-specific definition for {top['name']} was not available.",
        )
        fallback = (
            f"Condition overview: {definition}\n\n"
            f"Model interpretation: The model identified {top['name']} as the highest-ranked pattern with "
            f"{top['model_confidence'] * 100:.2f}% model confidence. Other model candidates "
            "remain possible.\n\nSafety note: This academic output is not a diagnosis and should be reviewed "
            "by a qualified healthcare professional."
        )
        if not self.generator:
            return {"text": fallback, "source": "deterministic_fallback", "model": None}
        prompt = f"""Convert this immutable structured result into a concise patient-readable report.
Begin with a section labelled 'Condition overview:' using the supplied condition_information.definition
to define {top['name']} in neutral, general medical terms. The definition must be educational only: do not
claim that the patient has the condition, and do not add treatment, medication, prognosis, prevalence,
causes, tests, or clinical recommendations that are absent from the structured result.

Then add a section labelled 'Model interpretation:' explaining the highest-ranked class, its exact
model confidence, the alternative candidates, and the available symptom evidence. End with a section
labelled 'Safety note:' stating that this is not a diagnosis and recommending assessment by a qualified
healthcare professional.

Do not add or rename disease candidates, symptoms, labs, probabilities, or risk claims. Do not change
any structured value. Use llm_questionnaire_context.questions and answers when present to summarize the
questionnaire findings; these answers may include information outside the ML dataset. Do not invent additional precautions. Use 'the model identified', retain uncertainty,
and keep the report concise.
STRUCTURED_RESULT={json.dumps(structured_result)}
"""
        try:
            response, model_name = self.generator(contents=prompt, config=None)
            text = getattr(response, "text", "") or ""
            return {"text": text.strip() or fallback, "source": "llm_explanation_only", "model": model_name}
        except Exception:
            return {"text": fallback, "source": "deterministic_fallback", "model": None}

    def independent_assessment(self, patient_case: dict[str, Any]) -> dict[str, Any]:
        """Run an LLM-only research baseline with no ML-derived input."""
        fallback = {
            "most_likely_condition": None,
            "ranked_conditions": [],
            "severity": "UNKNOWN",
            "supporting_information": [],
            "insufficient_information": True,
            "non_disease_explanation_possible": True,
            "uncertainty_message": "Insufficient evidence for reliable disease-risk prediction.",
            "confidence_label": "LLM-estimated likelihood; not a calibrated or medically validated probability.",
            "source": "llm_unavailable_abstention",
            "model": None,
        }
        if not self.generator:
            return fallback
        prompt = f'''You are an independent medical risk-assessment baseline for research.
Use ONLY this original patient case. It contains no ML predictions, probabilities, questions, or answers.
Do not diagnose, prescribe, or claim calibrated probability. Do not force a condition when evidence is insufficient.
Return strict JSON only with keys: most_likely_condition (string|null), ranked_conditions
(array of at most 5 objects with condition, llm_estimated_likelihood_percent number 0-100, rationale),
severity (LOW|MEDIUM|HIGH|CRITICAL|UNKNOWN), supporting_information (string array),
insufficient_information (boolean), non_disease_explanation_possible (boolean), uncertainty_message (string|null).
Use LLM-estimated likelihood as an estimate, not clinical probability. Mention exertion, muscular strain,
or injury as a possible alternative only when supported by the original case.
PATIENT_CASE={json.dumps(patient_case)}'''
        try:
            response, model_name = self.generator(
                contents=prompt, config=JSON_RESPONSE_CONFIG
            )
            text = (getattr(response, "text", "") or "").strip()
            payload = _parse_json_object(text)
            ranked = payload.get("ranked_conditions", [])[:5]
            if not isinstance(ranked, list):
                return fallback
            payload.update({
                "ranked_conditions": ranked,
                "confidence_label": "LLM-estimated likelihood; not a calibrated or medically validated probability.",
                "source": "llm_only_independent",
                "model": model_name,
            })
            return payload
        except Exception as exc:
            LOGGER.warning("LLM-only assessment unavailable: %s", exc)
            return fallback

    def generate_questionnaire(
        self, patient_case: dict[str, Any], candidates: list[dict[str, Any]], max_questions: int
    ) -> dict[str, Any]:
        """Create LLM-authored multiple-choice follow-up questions."""
        if not self.generator:
            raise RuntimeError("LLM questionnaire generation is unavailable. Configure a working Gemini API key and quota.")
        prompt = f'''Generate {max_questions} concise, patient-friendly medical follow-up questions.
Use the original patient case and the supplied initial ML candidates only to decide what information is useful.
Questions are allowed to cover symptoms, onset, duration, severity, triggers, exertion, injury, and red flags;
they are not restricted to the ML dataset vocabulary. Do not diagnose, prescribe treatment, or mention model scores.
Return strict JSON only: {{"questions": [{{"question_id": "q_001", "question_text": "...",
"answer_type": "multiple_choice", "options": ["option 1", "option 2", "option 3"], "purpose": "..."}}]}}.
Every question must have 2 to 4 concise selectable options. Do not include "None of the above"; the application adds it.
Use exactly one question per object, at most {max_questions}.
ORIGINAL_PATIENT_CASE={json.dumps(patient_case)}
INITIAL_ML_CANDIDATES={json.dumps(candidates)}'''
        response, model_name = self.generator(
            contents=prompt, config=JSON_RESPONSE_CONFIG
        )
        text = (getattr(response, "text", "") or "").strip()
        payload = _parse_json_object(text)
        questions = payload.get("questions", [])
        if not isinstance(questions, list) or not questions:
            raise ValueError("LLM returned no questionnaire questions.")
        cleaned = []
        for index, question in enumerate(questions[:max_questions], start=1):
            question_text = str(question.get("question_text", "")).strip()
            options = [str(option).strip() for option in question.get("options", []) if str(option).strip()]
            if not question_text or not 2 <= len(options) <= 4:
                continue
            if all(option.casefold() != "none of the above" for option in options):
                options.append("None of the above")
            cleaned.append({
                "question_id": f"q_{index:03d}",
                "question_text": question_text,
                "answer_type": "multiple_choice",
                "options": options,
                "purpose": str(question.get("purpose", "Clinical follow-up")).strip(),
                "generated_by": "llm",
            })
        if not cleaned:
            raise ValueError("LLM returned invalid questionnaire questions.")
        return {"questions": cleaned, "source": "llm_generated", "model": model_name}
