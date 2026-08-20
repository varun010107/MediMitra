"""Dataset-backed educational descriptions and non-prescriptive precautions."""

from __future__ import annotations

import csv
import re
from difflib import get_close_matches
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


class DiseaseInfoService:
    """Load the project's disease metadata without making it an ML feature."""

    _MEDICATION_TERMS = {
        "acetaminophen",
        "antibiotic",
        "antibiotics",
        "insulin",
        "medication",
        "medications",
        "medicine",
        "pain killer",
        "painkillers",
    }

    def __init__(self, data_dir: Path | str = DATA_DIR) -> None:
        data_dir = Path(data_dir)
        self.descriptions = self._load_descriptions(
            data_dir / "disease_descriptions.csv"
        )
        self.precautions = self._load_precautions(
            data_dir / "disease_precautions.csv"
        )

    @staticmethod
    def _rows(path: Path) -> list[list[str]]:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [
                [cell.strip() for cell in row]
                for row in csv.reader(handle)
                if row and row[0].strip()
            ]

    def _load_descriptions(self, path: Path) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        for row in self._rows(path):
            if len(row) >= 2 and row[1]:
                result[_key(row[0])] = {
                    "disease": row[0],
                    "definition": " ".join(row[1].split()),
                }
        return result

    def _load_precautions(self, path: Path) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for row in self._rows(path):
            result[_key(row[0])] = {
                "disease": row[0],
                "precautions": [item for item in row[1:] if item],
            }
        return result

    @staticmethod
    def _match_key(disease: str, values: dict[str, Any]) -> str | None:
        requested = _key(disease)
        if requested in values:
            return requested
        matches = get_close_matches(requested, values.keys(), n=1, cutoff=0.84)
        return matches[0] if matches else None

    def _safe_precautions(self, disease: str) -> list[str]:
        match = self._match_key(disease, self.precautions)
        raw_items = self.precautions.get(match or "", {}).get("precautions", [])
        output: list[str] = []
        for item in raw_items:
            normalized = " ".join(item.split()).strip(" .")
            lowered = normalized.casefold()
            if any(term in lowered for term in self._MEDICATION_TERMS):
                continue
            if "consult" in lowered:
                normalized = "Consult a qualified healthcare professional."
            elif lowered == "follow up":
                normalized = "Arrange follow-up with a healthcare professional."
            else:
                normalized = normalized[:1].upper() + normalized[1:] + "."
            if normalized not in output:
                output.append(normalized)

        if not output:
            output.append(
                "Consult a qualified healthcare professional for confirmation and individualized guidance."
            )
        output.extend(
            item
            for item in (
                "Monitor symptoms and seek prompt medical care if they become severe or worsen.",
                "Do not start, stop, or change medication based only on this screening result.",
            )
            if item not in output
        )
        return output

    def get(self, disease: str) -> dict[str, Any]:
        """Return display-only information; it is never passed to the classifier."""
        match = self._match_key(disease, self.descriptions)
        definition = self.descriptions.get(match or "", {}).get("definition")
        if not definition:
            definition = (
                f"{disease} is the highest-ranked condition label in this screening. "
                "A condition-specific definition was not available in the project metadata."
            )
        return {
            "disease": disease,
            "definition": definition,
            "precautions": self._safe_precautions(disease),
            "source": "project_disease_metadata",
            "used_by_disease_classifier": False,
            "clinically_validated": False,
            "notice": (
                "Educational metadata only. Precautions require professional review and do not replace clinical advice."
            ),
        }
