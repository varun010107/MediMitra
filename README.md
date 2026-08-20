# MediMitra: two-pass disease classification prototype

MediMitra is an academic clinical decision-support prototype. It maps free-text complaints to a fixed dataset vocabulary, runs a symptom-only disease classifier, selects follow-up symptoms from training-set statistics, and runs the same classifier again with newly confirmed symptoms.

It does **not** diagnose patients, estimate real-world disease probability, prescribe treatment, or replace a qualified healthcare professional. Displayed probabilities are ML `model_confidence` values for this synthetic/repetitive dataset only.

## Architecture

```text
free text / selected symptoms
        |
        v
dataset-constrained symptom mapper
        |
        v
same persisted ML model (Pass 1)
        |
        v
dataset-statistics question selector
        |
        v
checkbox answers: present / absent / unknown / asked
        |
        v
same persisted ML model (Pass 2)
        |
        +--> separate unvalidated prototype RiskEngine
        |
        +--> optional LLM wording/explanation only
```

The LLM cannot select symptoms, change disease candidates, or change model confidences. Patient profile data and parsed lab reports remain separate and are not classifier features.

## Dataset and preprocessing

The supplied `dataset (Repaired).csv` was copied to `backend/data/disease_dataset.csv`; the original download was not modified. Actual inspection found:

- 4,920 rows and 18 columns
- target `Disease` plus `Symptom_1` through `Symptom_17`
- 41 balanced disease labels and 131 normalized symptoms
- 4,616 duplicated rows and only 304 unique disease-symptom patterns
- 3 to 17 symptoms per record (mean 7.45)

Symptoms are lowercased and converted to canonical underscore identifiers. A `MultiLabelBinarizer` creates the multi-hot input vector. The model intentionally uses symptoms only; age, gender, profile, lifestyle, medical history, and laboratory data are context fields because they are absent from this dataset.

## Setup and run

From the project directory in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

The code also works with a newer compatible Python version; development verification used Python 3.12.

Train or refresh the persisted artifacts (not required on every backend start):

```powershell
.\.venv\Scripts\python.exe -m backend.train_model
```

Print three reproducible Pass-1/Pass-2 examples:

```powershell
.\.venv\Scripts\python.exe -m backend.demo_predictions
```

Run the reproducible accuracy evaluation without overwriting the saved model:

```powershell
.\.venv\Scripts\python.exe -m backend.evaluate_accuracy
```

This command also regenerates the evaluation figures inside `backend/models/evaluation/`: accuracy comparison, masking curve, cross-validation folds, confusion matrix, disease-wise F1, confidence calibration, disease–symptom heatmap, Pass-1 versus Pass-2, and accuracy versus questionnaire count.

The questionnaire figures are an offline cross-validation replay. The evaluator hides 60% of every held-out pattern, offers three training-statistics-driven symptom options per question group, and answers those options from the dataset record. This measures the algorithm under controlled synthetic conditions; it is not a patient study or clinical validation.

Run the API on port 8001:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

In a second PowerShell terminal, run the frontend on port 3000:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:3000`. Vite proxies `/api` to the FastAPI server.

## Training and evaluation

Training uses an 80/20 stratified split with random seed 42. Logistic Regression and Random Forest are compared by weighted F1, macro F1, and top-k accuracy. Logistic Regression was selected deterministically after both models tied on the random split.

| Model | Accuracy | Weighted F1 | Macro F1 | Top-3 | Top-5 |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Random Forest | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

These perfect random-split scores are **not clinical performance**. Repeated rows put identical patterns in training and test partitions. A masking test gives a more useful stress check:

| Symptoms hidden | Top-1 | Top-3 | Top-5 |
|---:|---:|---:|---:|
| 0% | 1.000 | 1.000 | 1.000 |
| 20% | 0.997 | 1.000 | 1.000 |
| 40% | 0.978 | 1.000 | 1.000 |
| 60% | 0.856 | 0.985 | 0.994 |

A stricter duplicate-aware evaluation collapses the dataset to its 304 unique disease/symptom patterns. Both its stratified holdout and five-fold cross-validation score 100% on complete symptom lists, demonstrating how deterministic and separable this synthetic dataset is. When symptoms are hidden inside the unique-pattern cross-validation test folds, performance is more realistic:

| Test symptoms hidden | Top-1 | Top-3 | Top-5 |
|---:|---:|---:|---:|
| 20% | 1.000 | 1.000 | 1.000 |
| 40% | 0.977 | 1.000 | 1.000 |
| 60% | 0.757 | 0.957 | 0.984 |
| 80% | 0.326 | 0.520 | 0.553 |

Evaluation files are under `backend/models/evaluation/`, including the confusion matrix, disease-wise report, comparison table, masking test, and JSON metrics.

## API flow

### Pass 1 and questionnaire

`POST /api/generate-questionnaire`

```json
{
  "patient_name": "Demo Patient",
  "age": 35,
  "gender": "female",
  "medical_history": "",
  "symptom_description": "high fever, chills and sweating",
  "selected_symptoms": []
}
```

The response includes mapping evidence, sorted Pass-1 candidates, and up to eight dataset-driven checkbox questions. Each question offers canonical symptom options and `None of the above`.

### Pass 2 and analysis

`POST /api/analyze`

```json
{
  "patient_name": "Demo Patient",
  "age": 35,
  "gender": "female",
  "medical_history": "",
  "symptom_description": "high fever, chills and sweating",
  "selected_symptoms": [],
  "questionnaire": ["copy the returned structured question objects here"],
  "questionnaire_answers": {
    "q_1": ["headache", "nausea"],
    "q_2": ["none"]
  },
  "lab_report_text": ""
}
```

Multiple checked symptoms become present. Selecting `none` marks every displayed symptom absent and is mutually exclusive. Unchecked options remain unknown, while all displayed options become asked. Pass 2 unions the original and newly present symptoms and invokes the exact same saved model and encoder.

A request with no recognized symptoms returns HTTP 422 and mapping guidance instead of making a guess.

## Tests and build

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm run lint
npm run build
```

Tests cover normalization, synonyms, negation, unknown inputs, model loading, sorted top-k outputs, shared Pass-1/Pass-2 artifacts, question vocabulary/ranking and exclusions, checkbox state semantics, LLM immutability, zero-mapping rejection, and the end-to-end API flow.

## Important files

- `backend/train_model.py` — inspection, model comparison, masking evaluation, and artifact persistence.
- `backend/demo_predictions.py` — reproducible Pass-1/Pass-2 examples using saved artifacts.
- `backend/evaluate_accuracy.py` — duplicate-aware holdout, cross-validation, and incomplete-symptom stress testing.
- `backend/services/symptom_mapper.py` — controlled vocabulary mapping and explicit reviewed aliases.
- `backend/services/prediction_service.py` — shared Pass-1/Pass-2 model inference.
- `backend/services/question_selector.py` — candidate-weighted discrimination scoring from training-only statistics.
- `backend/services/patient_state.py` — present, absent, unknown, and asked state transitions.
- `backend/services/risk_engine.py` — separate configuration-driven prototype interface.
- `backend/services/llm_service.py` — optional wording/explanation layer with immutable structured facts.
- `backend/api/routes.py` — FastAPI schemas and orchestration.
- `frontend/src/pages/AIDiagnosis.jsx` — two-pass clinical prototype UI.
- `backend/models/` — persisted model/encoders/metadata; backend startup only loads these files.

## Remaining integration and validation work

- Replace the current batch follow-up selection with live question-by-question re-ranking if desired.
- Add clinically reviewed risk rules before any real-world use. Current rules are explicitly unvalidated placeholders.
- Validate symptom synonyms, negation, demographics, and language handling with clinicians and representative users.
- Train on a patient-level, independently sourced, clinically governed dataset before interpreting confidence clinically.
- Connect Gemini only for approved wording and final narrative generation; the deterministic fallback already works without an API key.
- Connect a validated lab parser and future context/risk models separately; lab/profile fields must not enter this classifier version.
- Add authentication, consent, audit logging, privacy controls, monitoring, and deployment security before handling real patient information.

## Medical disclaimer

For education and research only. Outputs are model-generated candidate labels, not confirmed diagnoses. Seek a qualified healthcare professional for medical assessment. Urgent or severe symptoms require appropriate emergency services; do not rely on this prototype for triage.
