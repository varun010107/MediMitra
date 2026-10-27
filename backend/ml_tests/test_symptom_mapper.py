from pathlib import Path

from backend.services.symptom_mapper import SymptomMapper, canonicalize_symptom

VOCAB = Path(__file__).resolve().parents[1] / "data" / "symptom_vocabulary.json"


def test_canonical_normalization() -> None:
    assert canonicalize_symptom(" skin_rash ") == "skin_rash"
    assert canonicalize_symptom("dischromic _patches") == "dischromic_patches"


def test_exact_mapping() -> None:
    result = SymptomMapper(VOCAB).map_text("I have skin rash and vomiting")
    assert {"skin_rash", "vomiting"} <= set(result["present_symptoms"])


def test_synonym_mapping() -> None:
    result = SymptomMapper(VOCAB).map_text("My whole body hurts and I feel very tired")
    assert {"muscle_pain", "fatigue"} <= set(result["present_symptoms"])


def test_left_arm_pain_maps_to_supported_muscle_pain() -> None:
    result = SymptomMapper(VOCAB).map_text("I have pain in my left arm and left arm pain")

    assert "muscle_pain" in result["present_symptoms"]


def test_explicit_negation_maps_absent() -> None:
    result = SymptomMapper(VOCAB).map_text("I have fever but no rash")
    assert "skin_rash" in result["absent_symptoms"]
    assert "skin_rash" not in result["present_symptoms"]


def test_invalid_explicit_symptom_is_rejected() -> None:
    result = SymptomMapper(VOCAB).map_text("", ["invented_medical_feature"])
    assert result["present_symptoms"] == []
    assert result["invalid_explicit_symptoms"] == ["invented_medical_feature"]
