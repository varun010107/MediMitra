from backend.services.comparison_service import agreement_analysis, prediction_summary


def test_prediction_summary_marks_low_confidence_as_uncertain() -> None:
    summary = prediction_summary([
        {"disease": "A", "model_confidence": 0.15},
        {"disease": "B", "model_confidence": 0.14},
    ])

    assert summary["uncertain"] is True
    assert summary["top_1_top_2_margin"] == 0.01


def test_agreement_statuses_are_computed_from_leading_labels() -> None:
    result = agreement_analysis(
        {"most_likely_condition": "A"},
        {"summary": {"top_prediction": "A"}},
        {"summary": {"top_prediction": "B"}},
    )

    assert result["status"] == "partial_agreement"
