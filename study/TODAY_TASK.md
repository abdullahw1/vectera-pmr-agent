# Today's Task: Finish the Evidence-Grounded Reporting Agent

Superseded by FINAL_TASK_LIST.md after the source/code audit on October 2. This document records the earlier plan; follow FINAL_TASK_LIST.md for current priorities, added numerical-fidelity work, estimates, and completion gates. REQUIREMENTS_AUDIT.md explains the changes and Claude suggestion decisions.

Date: Friday, October 2, 2026, America/Los_Angeles.
Target submission: Saturday, October 3, end of day in the user's time zone, based on the email's four-calendar-day wording.

This is a work plan, not a completed-work claim. It reflects the interview context provided by Abdullah. It is personal planning material and is outside the submission packager's included folders.

## Objective

Finish implementation today of a small, demonstrably agentic reporting system whose financial engine remains deterministic. Differentiate through inspectable actions, source accountability, tested failure behavior, meaningful-output repeatability, and a simple handoff. No hiring outcome can be guaranteed, and competitors' implementation quality is unknown.

Tomorrow is reserved for live extraction verification, human review, target-environment checks, interview preparation, and submission. A defect discovered tomorrow may still require a narrowly scoped fix; "code complete" is not a promise to ignore defects.

## Keep

- Existing Python financial formulas, source precedence, role selection, committee event processing, compliance, and reconciliation.
- PyMuPDF, openpyxl, ReportLab, Matplotlib, the existing provider boundary, and portable Python 3.12 execution.
- Source locators and calculation-input relationships in the evidence ledger.
- Warning/blocker separation, constrained chart corrections, and human finalization.
- One-command native launcher and explicit no-key degradation.
- Existing tests, extending them rather than replacing the application.

## Remove or Replace

- Replace the scattered one-shot model quotation-selection path with one bounded evidence-investigation loop. Keep source-only extraction as fallback.
- Stop letting model-selected highlights or incidental response order determine numerical market-exhibit selection. Apply documented deterministic presentation rules to validated extracted data.
- Replace financial-only repeatability acceptance with a canonical comparison of all meaningful report outputs, including chart data and reported numerical narrative facts. Keep financial-only diagnostics, but do not label them complete repeatability proof.
- Remove any description suggesting a cache hit proves independent clean-run reproducibility, or a typed reviewer name provides authenticated approval.
- Remove arbitrary first-three-chart truncation as the only relevance rule; inspect all chart extractions and use a stable, documented concise presentation policy.
- Remove stale completion claims and draft-only packaging assumptions. Final artifacts must be included and clearly distinguished from drafts.
- Do not remove useful financial safeguards or existing user changes.

## Add: One Bounded Agent, Not a Multi-Agent System

Goal: investigate supporting evidence for the already determined report requirements, return verifiable source references, and expose unresolved gaps to the reviewer.

The model chooses a structured action, code validates and executes it, the model receives the observation, and it chooses another action or stops. This action-observation-decision loop is the agentic feature.

Candidate tools:

- List eligible document IDs and source metadata.
- Search passages within a supplied client/period/entity-scoped evidence collection.
- Inspect a passage by its registered ID and source locator.
- Submit evidence references for validation against the predefined requirement.
- Finish with an evidence assessment or explicitly escalate a gap.

Tool names and arguments are schema-validated. Registered document/passage IDs, not arbitrary filesystem paths, define access. No shell, network browsing, source editing, financial overrides, or approval tools.

The agent cannot change selected funds, financial results, client policies, benchmark ownership, required structure, or report ordering. An exact quotation containing different numerical facts is not dismissed as merely a prose variation.

Use deterministic retrieval and explicit source filters rather than embeddings or a new vector database. Define a small retrieval interface that could later be backed by Vectera's shared RAG service; do not pretend that integration exists now.

Use the existing provider transport with validated structured actions and explicit loop state. No new agent framework by default: the required loop is small enough to inspect directly. Record the rationale. A framework is not the evidence that this is an agent; model-directed tool choice and feedback are.

Budget the loop globally, initially at no more than eight actions per report, within the existing shared model-time budget. Repeated identical actions, invalid arguments, missing keys, provider failures, and exhausted budgets have explicit stop/fallback behavior. These limits are generic operational configuration, not quarter-specific facts.

Output an execution manifest containing validated actions, observations, returned source IDs, validation decisions, and stop reason. Do not request, log, or display private chain-of-thought. Operational traces are enough.

## Repeatability Boundary

Agent action order may vary, but the required report results must not.

Code controls the complete eligible evidence inventory and deterministic assembly. Agent assessments are useful review evidence, not unvalidated authority. Use stable source selection for numerical passages; do not allow model choices to change reported figures unnoticed.

For vision data, validate schema, labels, units, duplicate keys, finite values, and explicit uncertainty. Canonicalize ordering, not values: sorting a response cannot fix a different number. Do not invent chart bounds or infer unlabelled points.

Compare independent, uncached extractions on actual images. Agreement is useful evidence, not proof of correctness. Disagreement must block finalization or be resolved through additional verified extraction and human review, not averaged away or silently rounded until equal.

A reviewed extraction replay must be tied to source bytes and extraction configuration. Report replay, warm-cache behavior, and independent fresh extraction are separate modes with separate claims. If fresh vision results fail the spec's repeatability standard, surface that as an unresolved acceptance gap rather than marking the test passed.

## Work Packages

### 1. Agent and Retrieval Boundary: 2-3 Hours

- Extract a source-scoped passage inventory from existing parsers.
- Implement the restricted retrieval tools and validated agent loop.
- Persist the operational trace and make evidence assessment visible in review.
- Replace redundant model quotation selection with this path, retaining safe fallback.

Acceptance: a test demonstrates that the second action depends on the first tool observation; fabricated source IDs and unscoped access are rejected; missing evidence is escalated; action/budget limits work; financial results remain unchanged.

### 2. Chart and Meaningful-Output Controls: 2-3 Hours

- Centralize chart-response and correction validation.
- Remove model-controlled numeric presentation order/highlight selection where it affects repeatability.
- Create canonical meaningful-result signatures that include chart values, relevant labels and units, numerical facts appearing in commentary, fund roles/order, compliance, and section structure.
- Make independent-run comparisons fail on a changed figure even if financial totals match.
- Record extraction configuration and distinguish replay from fresh calls.

Acceptance: intentionally changing one chart value or narrative figure fails comparison; ordering-only changes normalize appropriately; malformed units/labels and uncertain readings are surfaced; no financial source value is silently repaired.

### 3. Unseen-Input and Failure Tests: 1.5-2.5 Hours

- Extend end-to-end fixtures, not only isolated finance tests: a different period/client with supported contracts, moved rows, changed filenames, an added zero-balance fund, missing manager support, and changed committee chronology.
- Add ambiguous candidate sources, missing numeric values, unavailable required PDF text, malformed model output, duplicate chart series, source changes during review, and provider failure.
- Treat unsupported scanned or damaged documents as clearly identified limitations/blockers, not a rushed promise of general OCR.
- Publish a concise fixture/results matrix with expected behavior and observed outcomes. Mark unexecuted tests explicitly.

Acceptance: changes within the stated contract complete without production code edits; invalid inputs either create a clearly identified safe draft or fail with actionable diagnostics; no false finalization.

### 4. Handoff and Finalization Hardening: 1-1.5 Hours

- Verify launcher argument forwarding and native path handling through tests; arrange actual Windows execution separately.
- Keep review-server binding local and handle startup failures clearly.
- Check server-side review acknowledgment and finalization preconditions, while retaining honest authentication limitations.
- Include final report, approval record, final evidence, agent trace, and current verification artifacts in packaging when present.
- Validate archive contents, missing required deliverables, and exclusion of credentials/environments/caches.

Acceptance: packaging cannot silently present a draft as an approved final; the archive contains matching reviewed artifacts; one-command instructions state real prerequisites.

### 5. Documentation and Freeze: 1-2 Hours

- Update the short write-up with the agent-versus-code boundary, bounded retrieval, reproducibility scope, shared-RAG integration point, and limitations.
- Add one architecture diagram, a compact decision log, and actual verification results. Do not inflate the required write-up beyond two pages.
- Update the walkthrough to show one input change, one source trace, one agent action/observation sequence, and one blocked failure.
- Identify explanatory code simplifications where needed, without unrelated refactoring.
- Refresh test artifacts and package only after relevant checks complete.

Acceptance: README, code, write-up, demo, and verification describe the same implemented system. Abdullah can locate the responsible module and explain each major decision.

## Scope and Schedule

Estimated coding effort: roughly 8-12 focused hours, with overlap between tests and implementation. This is an estimate, not a measured completion time. Start with the smallest agent loop; do not let agent polish consume the time needed to meet the spec.

Order: agent boundary; meaningful-output controls; adversarial/end-to-end tests; finalization and packaging; documentation freeze. Tests are developed alongside implementation, not left until the end. Full live/demo verification is a distinct completion step.

If time is tight, cut trace presentation polish, optional retrieval ranking sophistication, and extra fixtures before cutting required chart accuracy, numerical repeatability acceptance, or finalization safeguards.

If the initial agent implementation cannot meet its bounded acceptance checks quickly, simplify its tools and scope. Do not add a second agent or a framework migration to rescue it.

## Explicit Non-Goals

- Terraform, Kubernetes, hosted deployment, and unnecessary Docker prerequisites.
- Multiple specialized agents or an autonomous investment committee simulation.
- New embedding/vector infrastructure competing with their shared RAG engine.
- Free-form financial reasoning, fabricated missing facts, or AI approval of its own report.
- Arbitrary-layout/OCR support, unrestricted browser financial editing, or a new frontend framework.
- Claims that other candidates will perform poorly or that these changes guarantee an offer.

## Abdullah's Required Participation

- Supply a real provider key privately through the existing environment setup; never paste it into the chat or submission.
- Approve required local-network/API testing permissions when requested.
- Provide or arrange Windows access, or authorize using a repository/CI run; do not claim a hosted run before observing its result.
- Inspect extracted chart values and final PDF, then explicitly approve through the workflow.
- Reserve 60-90 minutes tomorrow for the walkthrough and code-understanding practice.

## Completion Gate

Coding complete today means the bounded agent, evidence tools, schemas, meaningful-output comparison, tests, packaging changes, and documentation exist and their locally executable checks pass. It does not mean the submission is automatically ready.

Submission ready requires actual live chart extraction, validation of all meaningful repeated-run outputs, human review, target-environment evidence or an honest disclosed limitation, refreshed final artifacts, and a truthful write-up. Defects and failed acceptance criteria remain visible even if the deadline is near.
