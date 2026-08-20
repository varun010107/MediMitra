"""MediMitra FastAPI application."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fpdf import FPDF
from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.api import routes

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="MediMitra API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
MODEL_FALLBACK_CHAIN = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]


def generate_with_fallback(contents, config=None):
    if not client:
        raise RuntimeError("Gemini is not configured")
    last_error = None
    for model_name in MODEL_FALLBACK_CHAIN:
        try:
            response = client.models.generate_content(
                model=model_name, contents=contents, config=config
            )
            return response, model_name
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"All Gemini models unavailable. Last error: {last_error}")


routes.configure_llm(generate_with_fallback if client else None)
app.include_router(routes.router)


@app.post("/api/parse-lab-report")
async def parse_lab_report(file: UploadFile = File(...)):
    """Preserved lab parser; lab output remains outside the disease classifier."""
    if not client:
        raise HTTPException(status_code=500, detail="AI lab parser not configured")
    try:
        file_bytes = await file.read()
        prompt = """Extract key test results from this lab report. Identify reported high/low values and summarize findings. Do not diagnose. Return structured text."""
        response, _ = generate_with_fallback(
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=file.content_type),
                prompt,
            ]
        )
        return {
            "summary": response.text,
            "used_by_disease_classifier": False,
            "component": "separate_lab_context",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class PDFRequest(BaseModel):
    patient_name: str
    age: int
    gender: str
    medical_history: str
    results: dict
    clinician_notes: str | None = None
    clinician_name: str | None = None


@app.post("/api/generate-pdf")
def generate_pdf(request: PDFRequest):
    """Preserved PDF report generation, adapted to structured ML output."""
    result = request.results
    primary = result.get("primary_pathology") or result.get("most_likely_condition", {}).get("name", "N/A")
    confidence = result.get("model_confidence")
    confidence_text = f"{float(confidence) * 100:.2f}% model confidence" if confidence is not None else "N/A"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(14, 124, 123)
    pdf.cell(0, 10, "MEDIMITRA - ACADEMIC SCREENING REPORT", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, "Educational prototype - not a medical diagnosis", ln=True)
    pdf.ln(5)
    pdf.set_text_color(20, 32, 31)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, f"Patient: {request.patient_name} | Age: {request.age} | Gender: {request.gender}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, f"History (context only): {request.medical_history or 'None reported'}")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"Highest-ranked model class: {primary}", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Risk: {result.get('triage_level', 'N/A')} | {confidence_text}", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, f"What is {primary}?", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0,
        5,
        result.get("condition_definition")
        or result.get("condition_information", {}).get("definition", "N/A"),
    )
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Model Explanation:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, result.get("clinical_reasoning_summary", "N/A"))
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Other Model Candidates (Pass 2):", ln=True)
    pdf.set_font("Helvetica", "", 10)
    alternatives = result.get("differential_diagnoses", [])
    if alternatives:
        for candidate in alternatives:
            name = candidate.get("name") or candidate.get("disease", "Unknown")
            score = float(candidate.get("model_confidence", 0)) * 100
            pdf.multi_cell(0, 5, f"- {name}: {score:.2f}% model confidence")
    else:
        pdf.multi_cell(0, 5, "No alternative candidates were returned.")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Precautionary Measures:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for precaution in result.get("precautionary_countermeasures", []):
        pdf.multi_cell(0, 5, f"- {precaution}")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Model confidence is not clinical certainty. Seek assessment from a qualified healthcare professional.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temporary:
        pdf.output(temporary.name)
        return FileResponse(
            temporary.name,
            media_type="application/pdf",
            filename=f"MediMitra_{request.patient_name}_Report.pdf",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
