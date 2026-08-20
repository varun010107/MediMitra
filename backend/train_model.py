"""Train and evaluate the symptom-only MediMitra disease classifier."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import matplotlib
import numpy as np
import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib"))
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    top_k_accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer

from backend.services.symptom_mapper import canonicalize_symptom, display_symptom

LOGGER = logging.getLogger(__name__)
RANDOM_STATE = 42
TEST_SIZE = 0.20
BASE = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = Path(__file__).resolve().parent / "data" / "disease_dataset.csv"
MODEL_DIR = Path(__file__).resolve().parent / "models"
DATA_DIR = Path(__file__).resolve().parent / "data"


def load_and_prepare(path: Path) -> tuple[pd.DataFrame, str, list[str], list[list[str]]]:
    """Read the wide symptom dataset and normalize each row into unique IDs."""
    frame = pd.read_csv(path)
    target = "Disease" if "Disease" in frame.columns else "prognosis" if "prognosis" in frame.columns else None
    if target is None:
        raise ValueError("Dataset must contain a Disease or prognosis target column")
    symptom_columns = sorted(
        [column for column in frame.columns if column.lower().startswith("symptom_")],
        key=lambda value: int(value.split("_")[-1]),
    )
    if not symptom_columns:
        raise ValueError("Dataset contains no Symptom_1...Symptom_17 columns")
    symptom_rows: list[list[str]] = []
    for values in frame[symptom_columns].itertuples(index=False, name=None):
        normalized = [canonicalize_symptom(value) for value in values if pd.notna(value)]
        symptom_rows.append(list(dict.fromkeys(item for item in normalized if item)))
    prepared = frame.copy()
    prepared[target] = prepared[target].astype(str).str.strip()
    return prepared, target, symptom_columns, symptom_rows


def metric_bundle(y_true: np.ndarray, y_pred: np.ndarray, proba: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    """Calculate required multiclass metrics from actual predictions."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "weighted_precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "weighted_recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "top_3_accuracy": float(top_k_accuracy_score(y_true, proba, k=min(3, proba.shape[1]), labels=labels)),
        "top_5_accuracy": float(top_k_accuracy_score(y_true, proba, k=min(5, proba.shape[1]), labels=labels)),
    }


def evaluate(model: Any, x_test: np.ndarray, y_test: np.ndarray) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    proba = model.predict_proba(x_test)
    pred = model.predict(x_test)
    return metric_bundle(y_test, pred, proba, np.asarray(model.classes_)), pred, proba


def mask_present_features(x_test: np.ndarray, fraction: float, seed: int) -> np.ndarray:
    """Randomly hide a fraction of each test patient's present symptoms."""
    rng = np.random.default_rng(seed)
    masked = x_test.copy()
    for row_index in range(masked.shape[0]):
        present = np.flatnonzero(masked[row_index])
        if len(present) <= 1:
            continue
        count = min(len(present) - 1, int(round(len(present) * fraction)))
        if count:
            masked[row_index, rng.choice(present, size=count, replace=False)] = 0
    return masked


def build_disease_symptom_stats(
    diseases: list[str], symptom_rows: list[list[str]], vocabulary: list[str]
) -> dict[str, dict[str, float]]:
    """Estimate P(symptom present | disease) from training rows only."""
    totals: dict[str, int] = {}
    counts: dict[str, dict[str, int]] = {}
    for disease, symptoms in zip(diseases, symptom_rows, strict=True):
        totals[disease] = totals.get(disease, 0) + 1
        disease_counts = counts.setdefault(disease, {})
        for symptom in symptoms:
            disease_counts[symptom] = disease_counts.get(symptom, 0) + 1
    return {
        disease: {
            symptom: round(counts.get(disease, {}).get(symptom, 0) / totals[disease], 8)
            for symptom in vocabulary
        }
        for disease in sorted(totals)
    }


def save_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, classes: list[str], path: Path) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=np.arange(len(classes)))
    plt.figure(figsize=(18, 15))
    sns.heatmap(matrix, cmap="Blues", xticklabels=classes, yticklabels=classes)
    plt.title("MediMitra held-out confusion matrix (random split)")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.xticks(rotation=60, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(path, dpi=170, bbox_inches="tight")
    plt.close()


def train(dataset_path: Path = DEFAULT_DATASET) -> dict[str, Any]:
    frame, target, symptom_columns, symptom_rows = load_and_prepare(dataset_path)
    vocabulary = sorted({symptom for row in symptom_rows for symptom in row})
    label_encoder = LabelEncoder().fit(frame[target])
    symptom_encoder = MultiLabelBinarizer(classes=vocabulary).fit([vocabulary])
    x = symptom_encoder.transform(symptom_rows)
    y = label_encoder.transform(frame[target])
    indices = np.arange(len(frame))
    train_idx, test_idx = train_test_split(
        indices, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    x_train, x_test = x[train_idx], x[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    candidates: dict[str, Any] = {
        "Logistic Regression": LogisticRegression(
            max_iter=2500, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=350,
            min_samples_leaf=1,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }
    if importlib.util.find_spec("xgboost") is not None:
        from xgboost import XGBClassifier

        candidates["XGBoost"] = XGBClassifier(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.07,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

    evaluations: dict[str, dict[str, Any]] = {}
    comparison_rows = []
    for name, model in candidates.items():
        LOGGER.info("Training %s", name)
        model.fit(x_train, y_train)
        metrics, predictions, probabilities = evaluate(model, x_test, y_test)
        evaluations[name] = {
            "model": model,
            "metrics": metrics,
            "predictions": predictions,
            "probabilities": probabilities,
        }
        comparison_rows.append({"model": name, **metrics})

    comparison = pd.DataFrame(comparison_rows).sort_values(
        ["weighted_f1", "macro_f1", "top_3_accuracy"], ascending=False
    )
    selected_name = str(comparison.iloc[0]["model"])
    selected = evaluations[selected_name]

    robustness = []
    for fraction in (0.0, 0.2, 0.4, 0.6):
        masked = x_test if fraction == 0 else mask_present_features(x_test, fraction, RANDOM_STATE + int(fraction * 100))
        probabilities = selected["model"].predict_proba(masked)
        predictions = selected["model"].predict(masked)
        robustness.append({
            "masked_present_fraction": fraction,
            "top_1_accuracy": float(accuracy_score(y_test, predictions)),
            "top_3_accuracy": float(top_k_accuracy_score(y_test, probabilities, k=3, labels=selected["model"].classes_)),
            "top_5_accuracy": float(top_k_accuracy_score(y_test, probabilities, k=5, labels=selected["model"].classes_)),
        })

    train_diseases = frame.iloc[train_idx][target].tolist()
    train_symptom_rows = [symptom_rows[index] for index in train_idx]
    stats = build_disease_symptom_stats(train_diseases, train_symptom_rows, vocabulary)
    repeated_rows = int(frame.duplicated().sum())
    unique_patterns = len({(frame.iloc[index][target], tuple(symptom_rows[index])) for index in indices})
    warning = (
        "This dataset contains repeated disease-symptom patterns. Conventional random-split "
        "metrics can substantially overestimate generalization to new patients and are not clinical validation."
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    evaluation_dir = MODEL_DIR / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected["model"], MODEL_DIR / "disease_model.pkl")
    joblib.dump(symptom_encoder, MODEL_DIR / "symptom_encoder.pkl")
    joblib.dump(label_encoder, MODEL_DIR / "label_encoder.pkl")
    with (DATA_DIR / "symptom_vocabulary.json").open("w", encoding="utf-8") as handle:
        json.dump({"symptoms": vocabulary, "display_names": {item: display_symptom(item) for item in vocabulary}}, handle, indent=2)
    with (DATA_DIR / "disease_symptom_stats.json").open("w", encoding="utf-8") as handle:
        json.dump({"source": "training_partition_only", "statistics": stats}, handle, indent=2)

    comparison.to_csv(evaluation_dir / "model_comparison.csv", index=False)
    pd.DataFrame(robustness).to_csv(evaluation_dir / "masking_robustness.csv", index=False)
    report = classification_report(
        y_test,
        selected["predictions"],
        labels=np.arange(len(label_encoder.classes_)),
        target_names=label_encoder.classes_,
        output_dict=True,
        zero_division=0,
    )
    pd.DataFrame(report).transpose().to_csv(evaluation_dir / "classification_report.csv")
    save_confusion_matrix(
        y_test,
        selected["predictions"],
        label_encoder.classes_.tolist(),
        evaluation_dir / "confusion_matrix.png",
    )
    metadata = {
        "model_name": selected_name,
        "model_version": "2.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_rows": len(frame),
        "training_rows": len(train_idx),
        "test_rows": len(test_idx),
        "disease_count": len(label_encoder.classes_),
        "symptom_count": len(vocabulary),
        "symptom_columns": symptom_columns,
        "duplicate_rows": repeated_rows,
        "unique_disease_symptom_patterns": unique_patterns,
        "metrics": selected["metrics"],
        "masking_robustness": robustness,
        "warning": warning,
        "clinical_validation": False,
        "features": "symptoms_only",
    }
    with (MODEL_DIR / "model_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    with (evaluation_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump({"selected_model": selected_name, "metrics": selected["metrics"], "warning": warning}, handle, indent=2)

    print(comparison.to_string(index=False))
    print(pd.DataFrame(robustness).to_string(index=False))
    print(f"Selected model: {selected_name}")
    print(warning)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    train(args.dataset.resolve())


if __name__ == "__main__":
    main()
