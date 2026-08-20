"""Research comparison helpers for independent LLM, ML, and hybrid outputs."""

from __future__ import annotations

from typing import Any


UNCERTAIN_THRESHOLD = 0.20
MARGIN_THRESHOLD = 0.05


def prediction_summary(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize classifier scores without treating them as clinical probability."""
    top = predictions[0] if predictions else None
    second = predictions[1] if len(predictions) > 1 else None
    top_score = float(top["model_confidence"]) if top else 0.0
    second_score = float(second["model_confidence"]) if second else 0.0
    margin = round(top_score - second_score, 8)
    uncertain = not top or top_score < UNCERTAIN_THRESHOLD or margin < MARGIN_THRESHOLD
    return {
        "top_prediction": top["disease"] if top else None,
        "top_1_model_probability": top_score if top else None,
        "top_2_model_probability": second_score if second else None,
        "top_1_top_2_margin": margin if top else None,
        "uncertain": uncertain,
        "uncertainty_message": "Insufficient evidence for reliable disease-risk prediction." if uncertain else None,
        "confidence_label": "ML classifier probability; not a medically validated disease probability.",
    }


def agreement_analysis(llm_only: dict[str, Any], ml_only: dict[str, Any], hybrid: dict[str, Any]) -> dict[str, Any]:
    """Describe agreement based only on each pipeline's leading label."""
    leaders = {
        "llm_only": llm_only.get("most_likely_condition"),
        "ml_only": ml_only.get("summary", {}).get("top_prediction"),
        "hybrid_ml_llm": hybrid.get("summary", {}).get("top_prediction"),
    }
    present = [item for item in leaders.values() if item]
    unique = set(present)
    status = (
        "complete_agreement" if len(present) == 3 and len(unique) == 1
        else "partial_agreement" if len(unique) < len(present)
        else "disagreement"
    )
    return {"status": status, "leading_predictions": leaders}
