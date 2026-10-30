# MediMitra: LLM-based health screening

MediMitra asks follow-up questions tailored to a patient's details, medical history, symptoms, and optional lab findings. Gemini reviews the complete case and returns either a possible main condition with alternatives, or **Insufficient evidence** when it cannot reasonably distinguish a leading condition.

This is an educational prototype, not a confirmed diagnosis or validated triage system. AI output can be wrong. It requires review by a qualified healthcare professional.

## Current flow

1. Enter name, age, gender, and relevant history, medicines, or allergies. Names and contact numbers are not sent to Gemini.
2. Describe symptoms freely. The searchable symptom catalogue is grouped by body area. These optional shortcuts are not a restricted vocabulary or a set of conditions with proven prediction accuracy. Optionally upload a PDF/image lab report, then review and correct the extracted text.
3. Gemini chooses a batch of 6–12 distinct follow-up questions from that initial case. Each question explains why it matters and includes unknown/none choices. These questions are personalized to the intake; they are not regenerated after each answer. An additional free-text field captures details outside the choices.
4. Gemini assesses all initial information and answers together. The result shows a main possibility and alternatives only when there is reasonable supporting evidence. Low certainty can accompany tentative, evidence-linked possibilities. The app suppresses condition labels only when the LLM explicitly finds insufficient evidence for a useful leading explanation. Missing tests alone do not require abstention. Urgency remains separate from diagnostic certainty.
5. Download the same assessment as a PDF, with supporting reported facts, explanations in simple language, limitations, next steps, and the complete information used.

No persisted disease classifier, symptom encoder, fixed-vocabulary mapping, or dataset risk engine participates in this flow. There are no disease probability percentages. Report explanations are evidence summaries, not access to the model's internal reasoning. Evidence IDs are checked against supplied facts; this does not independently establish the medical correctness of a generated explanation.

## Setup

Python 3.11+ and Node.js compatible with Vite 8 are required.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set GEMINI_API_KEY in .env. GEMINI_MODEL is optional.
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

In a second terminal:

```sh
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Vite proxies `/api` to port 8001.

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell.

A working Gemini key and available quota are required. Missing configuration, invalid AI output, or provider failure produces a retryable 503 service error, not a fabricated assessment or an “insufficient evidence” medical result. Uploaded lab files are limited to 10 MB and PDF/PNG/JPEG formats. Patient-entered health context and lab attachments are sent to Google's Gemini service; obtain appropriate consent before use. The app has no patient database or authentication and is not ready for real patient deployment.

## API

- `POST /api/generate-questionnaire`: patient name, age, gender, medical history, symptom description, optional selected symptoms and lab report text. Returns structured questions and model identity.
- `POST /api/analyze`: the same intake, returned questionnaire, a question-ID-to-answer dictionary, and optional `additional_details`. Every question needs an exact listed answer; unknown choices are allowed. Both generation and analysis enforce 6–12 questions. Under-length or invalid generated questionnaires get one bounded regeneration attempt.
- `POST /api/parse-lab-report`: multipart file. Returns editable AI-extracted findings.
- `POST /api/generate-pdf`: patient details and the returned `results`. Generates an explainable report without another model call and without leaving patient PDF files on disk.

The final assessment has `status`, `certainty`, `summary`, nullable `primary_condition`, `other_possibilities`, `uncertainty_explanation`, `missing_information`, `next_steps`, `urgency`, `urgency_reason`, `warning_signs`, and the exact `evidence` items considered. Each condition includes an overview, an explanation, supporting evidence IDs, and uncertainties.

## Tests

```sh
python -m pytest backend/tests -q
cd frontend
npm run lint
npm run build
```

Tests use a mocked Gemini provider to cover the complete intake/question/assessment/report flow, abstention, invalid output, provider unavailability, evidence references, and questionnaire validation. They do not establish clinical accuracy or replace testing with an actual configured Gemini account.

The six-question minimum is a product choice, not a clinically validated accuracy threshold. Question count varies by missing case information rather than randomness. See `docs/PROJECT_ROADMAP.md` for a proposed evaluation dashboard, clinician review workflow, patient timeline, and curated source retrieval.

## Code map

- `backend/main.py`: API startup, Gemini configuration, lab extraction, PDF endpoint.
- `backend/api/routes.py`: intake validation and questionnaire/assessment orchestration.
- `backend/services/assessment_service.py`: typed LLM response schemas, prompts, evidence preparation, abstention rules.
- `backend/services/report_service.py`: paginated PDF rendering of the same explained assessment.
- `frontend/src/pages/AIDiagnosis.jsx`: intake, questions, assessment, and report download.
- `frontend/src/context/PatientContext.jsx`: patient state in React memory.
- `frontend/src/modules/skin/`: TrustSkin-AI skin-lesion UI served at `/skin`.

## Skin lesion analysis (TrustSkin-AI)

The same frontend also hosts the TrustSkin-AI HAM10000 skin-lesion research module at `/skin` (`/skin/analyze`, `/skin/research`, `/skin/models`, `/skin/about`). Its code lives in `frontend/src/modules/skin/`; its backend is the separate [TrustSkin-AI](https://github.com/varun010107/TrustSkin-AI) repository. Vite proxies `/api/skin/*` to that API on port 8000 (prefix stripped), while `/api/*` stays on MediMitra's API on port 8001.

`run_all.sh` starts both APIs and the frontend. Set `TRUSTSKIN_DIR` if TrustSkin-AI is not checked out next to this repository, and `TRUSTSKIN_PYTHON` to the Python inside its virtual environment. TrustSkin-AI needs its trained `results/` and `outputs/` artifacts restored locally; they are not in either repository.

The earlier tabular ML pipeline and the standalone Streamlit prototype were removed; they remain available in git history.
