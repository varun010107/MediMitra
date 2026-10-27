# MediMitra: a stronger project beyond LLM screening

## Recommended direction

Build a patient screening and clinician review platform with measurable evaluation. The LLM prepares an explainable draft; a clinician can review it, correct it, and record an outcome. This adds useful software engineering and research work without pretending that another model automatically makes the product accurate.

The current app implements an intake, case-dependent questionnaire, evidence-linked assessment, lab context extraction, and PDF export. The features below are proposals, not implemented features or established performance claims.

## 1. Evaluation and model comparison dashboard — first priority

Create a versioned set of de-identified, consented, clinician-reviewed cases. Begin development with fictional fixtures; do not label LLM-generated answers as ground truth.

Record model/prompt version, inputs, follow-up questions, final possibilities, abstention, elapsed time, provider errors, and reviewer decisions. Compare prompt and model versions against the same held-out cases. Show case counts and denominators, not just a single accuracy percentage.

Useful measurements:

- Clinician agreement with the leading possibility and top three possibilities.
- Unsupported factual claims and incorrect evidence citations.
- Inappropriate reassurance or urgency suggestions, reviewed by clinicians.
- Appropriate versus unnecessary abstention.
- Relevant question coverage and repeated-question rate.
- Completion/drop-off rate, latency, and cost per completed assessment.

Present changes by symptom category and case complexity. Keep evaluation cases separate from prompt-tuning cases. This creates a reproducible research contribution and an honest way to test whether the system improves.

## 2. Clinician review workspace — second priority

Add accounts, role permissions, consent, and a database before saving real health information. Give the clinician an inbox of draft assessments, original evidence, suggested possibilities, and missing information. Support accept/edit/reject actions, notes, review timestamps, and version history. Clearly distinguish AI drafts from clinician-reviewed reports.

Suggested entities: users, patient profiles, encounters, evidence items, questions, answers, assessment versions, clinician reviews, and consent records. Use PostgreSQL with migrations, server-side authorization, and audit events. Never make the UI alone responsible for access control.

## 3. Patient timeline and follow-up

Let patients record changes over time, previous consultations, and repeated lab measurements. Display a timeline of reported symptoms and clinician-reviewed outcomes. Preserve original lab units and reference ranges; require review of AI extraction before comparison. Do not treat incomplete time series as evidence that symptoms resolved.

## 4. Curated source retrieval

Add retrieval from a small, reviewed collection of health guidance. Store source URL, publisher, publication/review date, passage, and version. Link a claim to the passage that supports it. Test that the citation actually supports the claim; a citation alone is not validation. Do not let arbitrary uploaded text become clinical guidance.

## Suggested demonstration

Show one fictional patient journey: intake → 6–12 personalized questions → explained AI draft → clinician correction → reviewed PDF → follow-up timeline. Then show an evaluation dashboard comparing two prompt versions on a fixed reviewed case set. This demonstrates frontend design, APIs, relational data modelling, authorization, auditability, explainability, and research methodology.

## What would support accuracy claims

A larger symptom catalogue and a minimum question count improve intake coverage; neither establishes clinical accuracy. The 6-question minimum is a product rule, not a clinically validated threshold. Claims need independent evaluation on representative, governed patient data with clinical oversight. An ML component can be reconsidered later if it solves a defined problem and has an appropriate dataset.

## References informing the direction

- WHO, Ethics and governance of artificial intelligence for health: https://www.who.int/publications/i/item/9789240029200
- WHO, Regulatory considerations on artificial intelligence for health: https://www.who.int/publications/i/item/9789240078871
- NHS respiratory symptom information, for ordinary symptom terminology rather than diagnostic labels: https://www.nhs.uk/conditions/respiratory-tract-infection/

These sources do not validate MediMitra, its question minimum, its catalogue, or its predictions. The roadmap is a project design recommendation.
