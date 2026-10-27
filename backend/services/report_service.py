"""Readable, paginated PDF reports built from the same validated result as the UI."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph

from backend.services.assessment_service import Assessment, DISCLAIMER


def build_report(patient: dict, result: dict) -> bytes:
    # A Unicode font is bundled with reportlab on supported installations. Fall back
    # to its built-in font if unavailable; paragraphs wrap long names and input.
    font_dir = Path(__import__("reportlab").__file__).parent / "fonts"
    regular, bold = font_dir / "Vera.ttf", font_dir / "VeraBd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Report", str(regular)))
        pdfmetrics.registerFont(TTFont("ReportBold", str(bold)))
        normal_font, bold_font = "Report", "ReportBold"
    else:
        normal_font, bold_font = "Helvetica", "Helvetica-Bold"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportBody", fontName=normal_font, fontSize=10, leading=15, spaceAfter=8, alignment=TA_LEFT, wordWrap="CJK"))
    styles.add(ParagraphStyle(name="ReportTitle", fontName=bold_font, fontSize=21, leading=27, textColor=colors.HexColor("#064E63"), spaceAfter=10))
    styles.add(ParagraphStyle(name="ReportHeading", fontName=bold_font, fontSize=12, leading=17, textColor=colors.HexColor("#0A6E8A"), spaceBefore=12, spaceAfter=7, keepWithNext=True))
    story = []

    def text(value, style="ReportBody"):
        return Paragraph(escape(str(value)).replace("\n", "<br/>"), styles[style])

    def section(title, content):
        story.append(text(title, "ReportHeading"))
        for value in content:
            story.append(text(value))

    # Reapply abstention semantics even for a report supplied directly by a client.
    assessment = Assessment.model_validate({key: result[key] for key in Assessment.model_fields})
    result = {**result, **assessment.model_dump()}
    story.extend([text("MediMitra", "ReportTitle"), text("Your explainable AI screening report", "ReportHeading"), text(DISCLAIMER)])
    section("Patient and report details", [
        f"Patient: {patient['patient_name']}",
        f"Age: {patient['age']} | Gender: {patient['gender']}",
        f"Medical history: {patient.get('medical_history') or 'Not provided (unknown)'}",
        f"Created: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Assessment method: LLM only | Model: {result.get('model') or 'Not recorded'}",
    ])
    insufficient = result["status"] == "insufficient_evidence"
    section("Screening outcome", [
        "Insufficient evidence" if insufficient else f"Main possibility: {result['primary_condition']['name']}",
        result["summary"],
    ])
    section("Urgency and next steps", [
        f"Suggested urgency: {result['urgency']}. This is AI guidance, not a validated triage score.",
        result["urgency_reason"], *[f"- {item}" for item in result["next_steps"]],
    ])
    if result["warning_signs"]:
        section("Warning signs to watch for", [f"- {item}" for item in result["warning_signs"]])
    candidates = ([result["primary_condition"]] if result["primary_condition"] else []) + result["other_possibilities"]
    evidence = {item["id"]: item for item in result.get("evidence", [])}
    for index, candidate in enumerate(candidates):
        section(("Main possibility: " if index == 0 else "Other possibility: ") + candidate["name"], [
            candidate["overview"], "Why it may fit: " + candidate["explanation"],
            *[f"Reported evidence [{ref}]: {evidence[ref]['label']} - {evidence[ref]['text']}" for ref in candidate["evidence_ids"] if ref in evidence],
            *["Still uncertain: " + item for item in candidate["uncertainties"]],
        ])
    section("What remains uncertain", [result["uncertainty_explanation"], *[f"- {item}" for item in result["missing_information"]]])
    section("Information used in this assessment", [f"[{item['id']}] {item['label']}: {item['text']}" for item in result.get("evidence", [])])
    section("How to interpret this report", [
        "The AI used the reported information above to suggest explanations. These explanations summarize supporting facts and limitations; they do not prove a disease or reveal the AI's internal reasoning.",
        "No trained disease classifier or dataset confidence scores were used. Numerical disease probabilities are not provided. An examination or appropriate tests may change the assessment.",
        DISCLAIMER,
    ])
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=(210 * mm, 297 * mm), rightMargin=20 * mm, leftMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm, title="MediMitra screening report", author="MediMitra")

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont(normal_font, 8)
        canvas.setFillColor(colors.HexColor("#4A5568"))
        canvas.drawString(20 * mm, 12 * mm, "AI screening - not a confirmed diagnosis")
        canvas.drawRightString(190 * mm, 12 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
