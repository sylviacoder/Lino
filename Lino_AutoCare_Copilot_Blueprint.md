# Lino AutoCare Copilot

## Project goal

Build a source-grounded AI assistant for an autocare business. It will help customers and service advisers understand common vehicle symptoms, routine maintenance needs, tyre information, and available services. It will demonstrate practical LLM engineering, retrieval-augmented generation (RAG), API development, testing, containerization, CI/CD, cloud deployment, evaluation, and monitoring.

This is a decision-support and customer-education tool. It does not replace a qualified mechanic's physical inspection.

## Why this project is credible

- It connects directly to Sylvia Onyejimbe's professional experience in tyre retail, autocare operations and business analytics.
- It solves a recognizable business problem instead of presenting an isolated chatbot demo.
- It combines LLM work with production engineering and measurable quality controls.
- It can later integrate the existing predictive vehicle-maintenance model.

## Version 1: minimum viable product

The first working version will:

1. Accept a vehicle-maintenance or tyre question.
2. Search an approved collection of maintenance and service documents.
3. Generate a clear answer using only the retrieved information.
4. Show the source used for the answer.
5. State when the available documents do not support an answer.
6. Highlight urgent safety situations that require the vehicle to be stopped or inspected.

### Example questions

- Why does my steering wheel vibrate at higher speeds?
- What should be checked when the engine temperature is unusually high?
- How often should engine oil and the oil filter be changed?
- What does 225/55R18 mean on a tyre?
- What should be inspected before a long road trip?
- Which Lino services are relevant to my issue?

## Initial scope

### Included

- Common vehicle symptoms and safe next-step guidance
- Preventive-maintenance explanations
- Tyre sizing, condition, rotation, pressure, and replacement guidance
- Lino service descriptions and frequently asked questions
- Citations to approved source documents
- Feedback capture for answer evaluation

### Excluded from Version 1

- A definitive diagnosis without physical inspection
- Repair instructions for safety-critical work
- Invented prices, stock levels, service availability, or vehicle specifications
- Customer personal data
- Live booking, payment, or messaging actions
- Demand forecasting

## Safety and answer rules

- Use retrieved sources rather than the model's unsupported memory.
- Cite the document behind factual maintenance guidance.
- Say that there is insufficient information when retrieval confidence is low.
- Recommend professional inspection for ambiguous or safety-critical symptoms.
- Treat brake failure, severe overheating, smoke, fuel smell, loss of steering control, tyre blowout, and warning-light combinations as urgent.
- Never present a likely cause as a confirmed diagnosis.
- Do not expose customer, employee, or confidential business data.

## Proposed architecture

1. A user enters a question in the web interface.
2. The FastAPI backend validates the request.
3. A retrieval component searches indexed, approved documents.
4. The LLM receives the question, retrieved passages, and safety instructions.
5. The application returns a grounded answer, citations, confidence status, and safety notice when required.
6. An evaluation and logging layer records quality signals without storing sensitive user data.

## Delivery phases

### Phase 1 — Knowledge foundation

- Finalize the use cases and boundaries.
- Collect public, trustworthy maintenance references.
- Prepare Lino service information and FAQs from anonymized business records.
- Remove confidential or personally identifiable information.

### Phase 2 — Local RAG application

- Build document ingestion and chunking.
- Generate embeddings and create the searchable index.
- Implement grounded question answering.
- Build the FastAPI backend and simple web interface.
- Add citations and safe refusal behavior.

### Phase 3 — Quality controls

- Create a test set of normal, unsupported, and safety-critical questions.
- Measure retrieval relevance, citation accuracy, groundedness, and response usefulness.
- Add automated tests and feedback capture.

### Phase 4 — Production engineering

- Containerize the application with Docker.
- Add GitHub Actions for testing and build checks.
- Configure secrets outside the codebase.
- Add health checks, structured logs, and basic monitoring.

### Phase 5 — AWS portfolio deployment

- Deploy the containerized application using the AWS workflow selected for the portfolio.
- Verify the live application and document the architecture.
- Capture screenshots and deployment evidence for GitHub and LinkedIn.
- Delete chargeable practice resources after the project demonstration.

### Phase 6 — Predictive-maintenance integration

- Recover or retrain the engine-health model.
- Expose the model through a validated prediction endpoint.
- Allow the assistant to explain a model result without changing the underlying prediction.
- Monitor the ML prediction and LLM explanation separately.

## Portfolio success criteria

- Answers are supported by visible sources.
- Unsupported questions receive a clear limitation instead of a fabricated answer.
- Safety-critical questions trigger the correct warning behavior.
- Automated tests pass before deployment.
- The application runs locally and from a reproducible Docker image.
- CI/CD successfully validates application changes.
- The cloud deployment can be demonstrated and safely removed afterward.
- The README explains the business problem, architecture, evaluation, limitations, and results.

## First decision needed

Choose the LLM execution route:

- **Hosted API:** easier to build and deploy, but requires separate API billing.
- **Local open-source model:** avoids per-request API billing, but needs more laptop memory and a heavier deployment environment.

The codebase should keep this choice behind a provider interface so it can be changed later without rewriting the application.

## Current implementation status

- The approved PII-free knowledge foundation is complete.
- A local TF-IDF retrieval baseline searches maintenance guidance, tyre products, engine oils and confirmed service prices.
- The baseline returns source metadata, rejects low-confidence unrelated questions and raises urgent-safety notices.
- The next implementation step is a provider interface for grounded LLM answer generation. The retrieval baseline itself consumes no LLM API budget.
