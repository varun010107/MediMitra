"""Run reproducible accuracy tests without overwriting trained model artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib")
)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer

from backend.train_model import (
    DEFAULT_DATASET,
    MODEL_DIR,
    RANDOM_STATE,
    TEST_SIZE,
    evaluate,
    load_and_prepare,
    mask_present_features,
    metric_bundle,
)

EVALUATION_DIR = MODEL_DIR / "evaluation"


def build_model() -> LogisticRegression:
    """Return the same classifier configuration selected during training."""
    return LogisticRegression(
        max_iter=2500,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )


def unique_pattern_indices(
    diseases: list[str], symptom_rows: list[list[str]]
) -> np.ndarray:
    """Keep one row per disease and canonical symptom-set combination."""
    seen: set[tuple[str, tuple[str, ...]]] = set()
    indices: list[int] = []
    for index, (disease, symptoms) in enumerate(
        zip(diseases, symptom_rows, strict=True)
    ):
        key = disease, tuple(sorted(set(symptoms)))
        if key not in seen:
            seen.add(key)
            indices.append(index)
    return np.asarray(indices, dtype=int)


def calibration_table(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    source: str,
    bins: int = 10,
) -> pd.DataFrame:
    """Summarize multiclass top-label confidence calibration."""
    confidence = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == y_true
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    for index in range(bins):
        upper_inclusive = index == bins - 1
        mask = (confidence >= edges[index]) & (
            confidence <= edges[index + 1]
            if upper_inclusive
            else confidence < edges[index + 1]
        )
        if not mask.any():
            continue
        rows.append(
            {
                "source": source,
                "bin_lower": edges[index],
                "bin_upper": edges[index + 1],
                "mean_model_confidence": float(confidence[mask].mean()),
                "observed_accuracy": float(correct[mask].mean()),
                "count": int(mask.sum()),
            }
        )
    return pd.DataFrame(rows)


def simulate_questionnaire_cv(
    x: np.ndarray,
    y: np.ndarray,
    folds: StratifiedKFold,
    question_count: int = 8,
    group_size: int = 3,
    initial_hidden_fraction: float = 0.6,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Replay dataset answers through adaptive, training-only symptom ranking."""
    class_count = len(np.unique(y))
    all_probabilities = np.zeros((question_count + 1, len(y), class_count))
    for fold_number, (fold_train, fold_test) in enumerate(
        folds.split(x, y), start=1
    ):
        model = build_model().fit(x[fold_train], y[fold_train])
        disease_symptom_frequency = np.zeros((class_count, x.shape[1]))
        for disease_index in range(class_count):
            disease_rows = x[fold_train][y[fold_train] == disease_index]
            if len(disease_rows):
                disease_symptom_frequency[disease_index] = disease_rows.mean(axis=0)
        initial = mask_present_features(
            x[fold_test],
            initial_hidden_fraction,
            RANDOM_STATE + 100 + fold_number,
        )
        for local_index, global_index in enumerate(fold_test):
            current = initial[local_index].copy()
            true_symptoms = x[global_index]
            asked = np.zeros(x.shape[1], dtype=bool)
            for question_index in range(question_count + 1):
                probabilities = model.predict_proba(current.reshape(1, -1))[0]
                all_probabilities[question_index, global_index] = probabilities
                if question_index == question_count:
                    continue
                candidates = np.argsort(probabilities)[-5:][::-1]
                weights = probabilities[candidates]
                weights = weights / weights.sum()
                values = disease_symptom_frequency[candidates]
                means = np.sum(weights[:, None] * values, axis=0)
                variance = np.sum(
                    weights[:, None] * (values - means) ** 2, axis=0
                )
                relevance = values.max(axis=0)
                scores = variance * (0.5 + relevance)
                scores[(current > 0) | asked | (relevance <= 0)] = -np.inf
                eligible = np.flatnonzero(np.isfinite(scores))
                if not len(eligible):
                    continue
                ranked = eligible[np.argsort(scores[eligible])[::-1]]
                options = ranked[:group_size]
                asked[options] = True
                current[options] = true_symptoms[options]

    rows = []
    labels = np.arange(class_count)
    for question_index in range(question_count + 1):
        probabilities = all_probabilities[question_index]
        predictions = probabilities.argmax(axis=1)
        metrics = metric_bundle(y, predictions, probabilities, labels)
        rows.append(
            {
                "questions_answered": question_index,
                "initial_hidden_symptom_fraction": initial_hidden_fraction,
                "mean_true_class_confidence": float(
                    probabilities[np.arange(len(y)), y].mean()
                ),
                **metrics,
            }
        )
    return pd.DataFrame(rows), all_probabilities


def save_presentation_graphs(
    x_unique: np.ndarray,
    y_unique: np.ndarray,
    class_names: np.ndarray,
    vocabulary: list[str],
    complete_probabilities: np.ndarray,
    masked_probabilities: np.ndarray,
    questionnaire: pd.DataFrame,
) -> dict[str, float]:
    """Save the five presentation-focused evaluation graphs."""
    complete_predictions = complete_probabilities.argmax(axis=1)
    masked_predictions = masked_probabilities.argmax(axis=1)
    complete_report = classification_report(
        y_unique,
        complete_predictions,
        labels=np.arange(len(class_names)),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    masked_report = classification_report(
        y_unique,
        masked_predictions,
        labels=np.arange(len(class_names)),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    disease_rows = [
        {
            "disease": disease,
            "complete_symptoms_f1": complete_report[disease]["f1-score"],
            "60_percent_hidden_f1": masked_report[disease]["f1-score"],
            "support": masked_report[disease]["support"],
        }
        for disease in class_names
    ]
    disease_frame = pd.DataFrame(disease_rows).sort_values(
        "60_percent_hidden_f1"
    )
    disease_frame.to_csv(
        EVALUATION_DIR / "per_disease_f1.csv", index=False
    )
    plotted = disease_frame.melt(
        id_vars=["disease"],
        value_vars=["complete_symptoms_f1", "60_percent_hidden_f1"],
        var_name="input",
        value_name="f1",
    )
    plotted["input"] = plotted["input"].map(
        {
            "complete_symptoms_f1": "Complete symptoms",
            "60_percent_hidden_f1": "60% symptoms hidden",
        }
    )
    plt.figure(figsize=(12, 14))
    sns.barplot(data=plotted, y="disease", x="f1", hue="input")
    plt.xlim(0, 1.05)
    plt.xlabel("F1 score")
    plt.ylabel("Disease")
    plt.title("Disease-wise F1 under complete and incomplete reporting")
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "per_disease_f1.png", dpi=180)
    plt.close()

    calibration = pd.concat(
        [
            calibration_table(y_unique, complete_probabilities, "Complete symptoms"),
            calibration_table(y_unique, masked_probabilities, "60% symptoms hidden"),
        ],
        ignore_index=True,
    )
    calibration.to_csv(EVALUATION_DIR / "confidence_calibration.csv", index=False)
    plt.figure(figsize=(8, 7))
    for source, marker in (("Complete symptoms", "o"), ("60% symptoms hidden", "s")):
        subset = calibration[calibration["source"] == source]
        plt.plot(
            subset["mean_model_confidence"],
            subset["observed_accuracy"],
            marker=marker,
            linewidth=2,
            label=source,
        )
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Ideal calibration")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel("Mean model confidence")
    plt.ylabel("Observed accuracy")
    plt.title("Top-label confidence calibration")
    plt.legend()
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "confidence_calibration.png", dpi=180)
    plt.close()

    symptom_frequency = x_unique.mean(axis=0)
    top_symptom_indices = np.argsort(symptom_frequency)[-30:][::-1]
    heatmap_values = np.vstack(
        [
            x_unique[y_unique == disease_index][:, top_symptom_indices].mean(axis=0)
            for disease_index in range(len(class_names))
        ]
    )
    heatmap_frame = pd.DataFrame(
        heatmap_values,
        index=class_names,
        columns=[vocabulary[index].replace("_", " ") for index in top_symptom_indices],
    )
    heatmap_frame.to_csv(EVALUATION_DIR / "disease_symptom_heatmap.csv")
    plt.figure(figsize=(18, 14))
    sns.heatmap(heatmap_frame, cmap="YlGnBu", vmin=0, vmax=1)
    plt.xlabel("Frequent dataset symptom")
    plt.ylabel("Disease")
    plt.title("Disease–symptom frequency heatmap (30 most frequent symptoms)")
    plt.xticks(rotation=55, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "disease_symptom_heatmap.png", dpi=180)
    plt.close()

    questionnaire.to_csv(
        EVALUATION_DIR / "questionnaire_simulation.csv", index=False
    )
    comparison = questionnaire[
        questionnaire["questions_answered"].isin([0, questionnaire["questions_answered"].max()])
    ].copy()
    comparison["stage"] = comparison["questions_answered"].map(
        {0: "Pass 1", int(questionnaire["questions_answered"].max()): "Pass 2"}
    )
    comparison_chart = comparison.melt(
        id_vars=["stage"],
        value_vars=["accuracy", "mean_true_class_confidence"],
        var_name="metric",
        value_name="score",
    )
    comparison_chart["metric"] = comparison_chart["metric"].map(
        {
            "accuracy": "Top-1 accuracy",
            "mean_true_class_confidence": "Mean true-class confidence",
        }
    )
    plt.figure(figsize=(8, 6))
    sns.barplot(data=comparison_chart, x="stage", y="score", hue="metric")
    plt.ylim(0, 1.05)
    plt.xlabel("Prediction stage")
    plt.ylabel("Score")
    plt.title("Simulated Pass 1 vs Pass 2 (60% of symptoms initially hidden)")
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "pass1_vs_pass2.png", dpi=180)
    plt.close()

    plt.figure(figsize=(10, 6))
    for metric, label, marker in (
        ("accuracy", "Top-1", "o"),
        ("top_3_accuracy", "Top-3", "s"),
        ("top_5_accuracy", "Top-5", "^"),
    ):
        plt.plot(
            questionnaire["questions_answered"],
            questionnaire[metric] * 100,
            marker=marker,
            linewidth=2,
            label=label,
        )
    plt.ylim(0, 105)
    plt.xticks(questionnaire["questions_answered"])
    plt.xlabel("Question groups answered")
    plt.ylabel("Accuracy (%)")
    plt.title("Simulated questionnaire benefit on held-out symptom patterns")
    plt.legend(title="Metric")
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "accuracy_vs_questions.png", dpi=180)
    plt.close()

    confidence = complete_probabilities.max(axis=1)
    correct = complete_predictions == y_unique
    complete_ece = float(
        sum(
            abs(row["observed_accuracy"] - row["mean_model_confidence"])
            * row["count"]
            for row in calibration[calibration["source"] == "Complete symptoms"].to_dict("records")
        )
        / len(y_unique)
    )
    return {
        "complete_expected_calibration_error": complete_ece,
        "complete_mean_confidence": float(confidence.mean()),
        "complete_observed_accuracy": float(correct.mean()),
    }


def save_accuracy_graphs(
    summary_rows: list[dict[str, Any]],
    fold_rows: list[dict[str, float | int]],
    masking_rows: list[dict[str, float]],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: np.ndarray,
) -> None:
    """Save readable PNG charts for the reproducible evaluation results."""
    sns.set_theme(style="whitegrid")

    summary = pd.DataFrame(summary_rows)
    chart = summary.melt(
        id_vars=["test"],
        value_vars=["accuracy", "top_3_accuracy", "top_5_accuracy"],
        var_name="metric",
        value_name="score",
    )
    chart["metric"] = chart["metric"].map(
        {
            "accuracy": "Top-1 accuracy",
            "top_3_accuracy": "Top-3 accuracy",
            "top_5_accuracy": "Top-5 accuracy",
        }
    )
    chart["test"] = chart["test"].map(
        {
            "random_row_holdout": "Random row holdout",
            "unique_pattern_holdout": "Unique-pattern holdout",
            "unique_pattern_5_fold_cv": "Unique-pattern 5-fold CV",
        }
    )
    plt.figure(figsize=(11, 6))
    sns.barplot(data=chart, x="test", y="score", hue="metric")
    plt.ylim(0, 1.05)
    plt.xlabel("Evaluation method")
    plt.ylabel("Score")
    plt.title("MediMitra accuracy comparison on complete symptom lists")
    plt.xticks(rotation=12, ha="right")
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "accuracy_comparison.png", dpi=180)
    plt.close()

    masking = pd.DataFrame(
        [{"hidden_symptom_fraction": 0.0, **summary_rows[-1]}, *masking_rows]
    )
    plt.figure(figsize=(10, 6))
    for metric, label, marker in (
        ("accuracy", "Top-1", "o"),
        ("top_3_accuracy", "Top-3", "s"),
        ("top_5_accuracy", "Top-5", "^"),
    ):
        plt.plot(
            masking["hidden_symptom_fraction"] * 100,
            masking[metric] * 100,
            marker=marker,
            linewidth=2,
            label=label,
        )
    plt.ylim(0, 105)
    plt.xlabel("Symptoms hidden from each test record (%)")
    plt.ylabel("Accuracy (%)")
    plt.title("Accuracy under incomplete symptom reporting")
    plt.legend(title="Metric")
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "accuracy_masking_curve.png", dpi=180)
    plt.close()

    folds = pd.DataFrame(fold_rows)
    plt.figure(figsize=(9, 5))
    sns.barplot(data=folds, x="fold", y="accuracy", color="#0A6E8A")
    plt.ylim(0, 1.05)
    plt.xlabel("Cross-validation fold")
    plt.ylabel("Top-1 accuracy")
    plt.title("Unique-pattern five-fold cross-validation")
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "accuracy_cv_folds.png", dpi=180)
    plt.close()

    matrix = confusion_matrix(
        y_true, y_pred, labels=np.arange(len(class_names)), normalize="true"
    )
    plt.figure(figsize=(18, 15))
    sns.heatmap(
        matrix,
        cmap="Blues",
        vmin=0,
        vmax=1,
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.xlabel("Predicted disease")
    plt.ylabel("Actual disease")
    plt.title("Normalized confusion matrix: unique-pattern five-fold CV")
    plt.xticks(rotation=60, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(EVALUATION_DIR / "accuracy_confusion_matrix.png", dpi=180)
    plt.close()


def run_accuracy_tests(dataset_path: Path = DEFAULT_DATASET) -> dict[str, Any]:
    """Evaluate the selected model using duplicate-aware holdout and CV tests."""
    frame, target, _, symptom_rows = load_and_prepare(dataset_path)
    diseases = frame[target].tolist()
    vocabulary = sorted({symptom for row in symptom_rows for symptom in row})
    symptom_encoder = MultiLabelBinarizer(classes=vocabulary).fit([vocabulary])
    label_encoder = LabelEncoder().fit(diseases)
    x_all = symptom_encoder.transform(symptom_rows)
    y_all = label_encoder.transform(diseases)

    unique_idx = unique_pattern_indices(diseases, symptom_rows)
    x_unique = x_all[unique_idx]
    y_unique = y_all[unique_idx]
    train_idx, test_idx = train_test_split(
        np.arange(len(unique_idx)),
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_unique,
    )
    holdout_model = build_model().fit(x_unique[train_idx], y_unique[train_idx])
    holdout_metrics, _, _ = evaluate(
        holdout_model, x_unique[test_idx], y_unique[test_idx]
    )

    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_probabilities = cross_val_predict(
        build_model(), x_unique, y_unique, cv=folds, method="predict_proba"
    )
    cv_predictions = np.argmax(cv_probabilities, axis=1)
    cv_metrics = metric_bundle(
        y_unique,
        cv_predictions,
        cv_probabilities,
        np.arange(len(label_encoder.classes_)),
    )
    fold_rows: list[dict[str, float | int]] = []
    for fold_number, (fold_train, fold_test) in enumerate(
        folds.split(x_unique, y_unique), start=1
    ):
        model = build_model().fit(x_unique[fold_train], y_unique[fold_train])
        metrics, _, _ = evaluate(model, x_unique[fold_test], y_unique[fold_test])
        fold_rows.append({"fold": fold_number, **metrics})

    masking_rows: list[dict[str, float]] = []
    masked_probabilities_by_fraction: dict[float, np.ndarray] = {}
    for fraction in (0.2, 0.4, 0.6, 0.8):
        masked_probabilities = np.zeros(
            (len(y_unique), len(label_encoder.classes_)), dtype=float
        )
        for fold_number, (fold_train, fold_test) in enumerate(
            folds.split(x_unique, y_unique), start=1
        ):
            model = build_model().fit(x_unique[fold_train], y_unique[fold_train])
            masked_test = mask_present_features(
                x_unique[fold_test], fraction, RANDOM_STATE + fold_number
            )
            masked_probabilities[fold_test] = model.predict_proba(masked_test)
        masked_predictions = np.argmax(masked_probabilities, axis=1)
        metrics = metric_bundle(
            y_unique,
            masked_predictions,
            masked_probabilities,
            np.arange(len(label_encoder.classes_)),
        )
        masked_probabilities_by_fraction[fraction] = masked_probabilities
        masking_rows.append({"hidden_symptom_fraction": fraction, **metrics})

    questionnaire_frame, _ = simulate_questionnaire_cv(
        x_unique,
        y_unique,
        folds,
        question_count=8,
        group_size=3,
        initial_hidden_fraction=0.6,
    )

    with (MODEL_DIR / "model_metadata.json").open(encoding="utf-8") as handle:
        metadata = json.load(handle)
    random_metrics = metadata["metrics"]
    summary_rows = [
        {"test": "random_row_holdout", "evaluated_rows": metadata["test_rows"], **random_metrics},
        {"test": "unique_pattern_holdout", "evaluated_rows": len(test_idx), **holdout_metrics},
        {"test": "unique_pattern_5_fold_cv", "evaluated_rows": len(unique_idx), **cv_metrics},
    ]
    warning = (
        "Metrics measure performance on this synthetic dataset, not diagnostic "
        "accuracy in real patients. The random-row holdout is inflated by duplicates."
    )
    result = {
        "dataset_rows": len(frame),
        "unique_disease_symptom_patterns": len(unique_idx),
        "duplicate_or_repeated_pattern_rows": len(frame) - len(unique_idx),
        "random_row_holdout": random_metrics,
        "unique_pattern_holdout": holdout_metrics,
        "unique_pattern_5_fold_cv": cv_metrics,
        "unique_pattern_5_fold_masking": masking_rows,
        "questionnaire_simulation": questionnaire_frame.to_dict("records"),
        "questionnaire_simulation_notice": (
            "Offline cross-validation replay: 60% of each test pattern is hidden, "
            "and dataset truth answers each offered symptom. This is not a clinical trial."
        ),
        "warning": warning,
    }
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary_rows).to_csv(
        EVALUATION_DIR / "accuracy_test_summary.csv", index=False
    )
    pd.DataFrame(fold_rows).to_csv(
        EVALUATION_DIR / "accuracy_test_cv_folds.csv", index=False
    )
    pd.DataFrame(masking_rows).to_csv(
        EVALUATION_DIR / "accuracy_test_masking.csv", index=False
    )
    pd.DataFrame(
        classification_report(
            y_unique,
            cv_predictions,
            labels=np.arange(len(label_encoder.classes_)),
            target_names=label_encoder.classes_,
            output_dict=True,
            zero_division=0,
        )
    ).transpose().to_csv(
        EVALUATION_DIR / "accuracy_test_classification_report.csv"
    )
    with (EVALUATION_DIR / "accuracy_test_results.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(result, handle, indent=2)

    save_accuracy_graphs(
        summary_rows,
        fold_rows,
        masking_rows,
        y_unique,
        cv_predictions,
        label_encoder.classes_,
    )
    calibration_metrics = save_presentation_graphs(
        x_unique,
        y_unique,
        label_encoder.classes_,
        vocabulary,
        cv_probabilities,
        masked_probabilities_by_fraction[0.6],
        questionnaire_frame,
    )
    result["calibration"] = calibration_metrics
    with (EVALUATION_DIR / "accuracy_test_results.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(result, handle, indent=2)

    print(pd.DataFrame(summary_rows).to_string(index=False))
    print("\nFive-fold unique-pattern accuracy by fold:")
    print(pd.DataFrame(fold_rows)[["fold", "accuracy", "macro_f1"]].to_string(index=False))
    print("\nUnique-pattern CV with symptoms hidden from each test record:")
    print(
        pd.DataFrame(masking_rows)[
            ["hidden_symptom_fraction", "accuracy", "top_3_accuracy", "top_5_accuracy"]
        ].to_string(index=False)
    )
    print("\nQuestionnaire simulation from 60% hidden symptoms:")
    print(
        questionnaire_frame[
            [
                "questions_answered",
                "accuracy",
                "top_3_accuracy",
                "top_5_accuracy",
                "mean_true_class_confidence",
            ]
        ].to_string(index=False)
    )
    print(f"\n{warning}")
    return result


if __name__ == "__main__":
    run_accuracy_tests()
