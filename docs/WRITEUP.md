# Vectera PMR Generator: Write-up

## Where the model stops and code starts

The rule I followed: if a step decides a number, a ranking, a filter or a pass/fail result, it is Python. If it needs reading or writing judgment, it is a model, and code checks the model's output before it reaches the report.

Code does all of the following: discovering and classifying input files, reading the flash by labels and headers, footing every fund, sleeve and portfolio total to the cent, computing dollar attribution (income + appreciation - fees), ranking the top two contributors, detractors and positions, applying the four IC-log filters with withdrawals and lapses, computing open approvals and the committed-or-approved totals, parsing guideline limits from the prior PMR, running the four compliance checks, and computing the direction of the office cap-rate gap. Every role and figure sentence in the report is a code template.

A model does two jobs. First, it reads the outlook deck's chart images, because those numbers exist only in pixels. Each reading is checked against its available axis bounds, keeps its slide locator, and requires human confirmation before approval. Second, it writes connecting prose for featured funds, new commitments and the market update. The writer receives numerical placeholders rather than raw figures. Each sentence cites a registered passage; code restores exact source strings and rejects additions, omissions, changed signs or units, and borrowing numbers from another passage. This does not prove English meaning: a second model pass checks each sentence against its quote, and human review remains required. Failed prose falls back to a complete, attributed source excerpt.

## How I know the output is correct

The tests include golden assertions for this quarter: the four featured funds and roles, $456.8M committed or approved across 14 positions, both new commitments, withdrawals and lapses, and compliance actuals. These are test fixtures only, never pipeline constants. Perturbations cover shuffled and moved rows, renamed files, zero-balance funds, a one-cent cash error, unknown IC actions, conflicting amounts, missing cash rows, renamed or unextractable manager headings, fabricated quotes and tampered approvals. Context regressions distinguish changed numeric source bindings from harmless diagnostic ID drift. Appendix tests walk every table cell back to the source PDF. A combined changed-client/period test stacks renamed benchmark and diversification labels, swapped cash columns, a renamed manager heading and a stray file, requiring identical figures, roles and compliance.

The supplied package has 58 reconciliation checks; currency mismatches block release. Repeatability runs use separate processes and empty caches, comparing every figure, chart reading, selection, role, compliance result and section. Model-prose numbers are also bound to scoped source text, locators and surrounding source context, rather than compared only as a bag of digits. Audit IDs can change with diagnostic metadata without changing those facts. English wording may vary; semantic paraphrase correctness still needs review. Saved records show the observed results, not a guarantee for all future model calls. CI is configured for Windows and macOS; a fresh-install script independently unpacks the submission and runs pinned installation, the full tests and no-key generation on the recorded host.

## Human review, warnings and blockers

A live run caught omitted risk dates in fallback prose. Fixed fallbacks preserve the writer's complete, scoped numerical inventory; regression tests reject changed source context.

The review page separates Report, Charts and Issues. Clicking text or table cells shows source locators and calculation inputs, including appendix bounding boxes. Chart corrections need reasons and revoke confirmation. They create a new draft, never immediate release: changed market evidence invalidates old prose, triggers checked rewriting or verified-observation fallback, and requires renewed report and chart review. Approval requires all charts confirmed, no blockers, a named reviewer and explicit acknowledgment. The backend refuses changed draft JSON, displayed PDF, inputs, implementation or exhibits. The approval record binds both draft and final PDF hashes.

A warning asks for inspection: missing manager evidence, unresolved document matches or paraphrases. A matched but unextractable report is retained as page evidence, never called absent. Blockers prevent release. Missing cash rows preserve holdings and NAV but suppress contribution rankings; blank holding NAVs retain funded status and cell evidence but suppress position rankings. Unresolved IC amounts make the combined approval total unavailable, not a partial sum. Recoverable gaps produce blocked drafts; unreadable required inputs stop generation explicitly.

## Next quarter and format changes

Next quarter, drop the new package into the inputs folder and run with the new client code and quarter. Nothing client- or quarter-specific is in the code. The client's full name and benchmark come from the flash. Guideline limits, the allocation policy, managers and disclosures come from the prior PMR. The IC logs are found by their columns, across years, so an approval made last year and still open is counted. Rows, fund counts and filenames can change because everything is located by labels and headers. A rehearsal script builds a different client for 1Q26, with renamed files, moved rows, one fund removed and two added, and an approval carried from a 2025 log into a 2026 withdrawal. It runs end to end without code changes.

For format changes, the section order and typography are read from the prior PMR's contents page and fonts. If the prior report gains a section the system does not know, it flags it rather than guessing. Section text is template code in one module, so a wording or layout change is a small, local edit. A new financial measure would need new code, and I would rather say so than pretend otherwise.

The appendix retains every current flash column, including horizons not shown in the prior report, split into portrait tables. Headers expand source abbreviations; currency and accounting signs decorate, never alter, the source values. The manifest records both displayed cells and raw source strings. Main charts are native ReportLab vectors; presentation tests check typography, emphasis, table borders and portrait dimensions.

## Briefly

Architecture: a single pipeline (discover, compute, gather evidence, write, render), with one shared evidence ledger that every figure and sentence registers in. A small local browser workspace sits on top for analysts, and the CLI does the same thing without it.

Traceability: manifest.json lists report blocks and individual table cells, including the appendix, with resolved evidence and source locators; evidence.json holds every fact, formula and input.

Ambiguity and entity resolution: names are matched by explicit, logged rules for legal suffixes, punctuation, Roman, Arabic and word numerals, "&" and a few abbreviations. Near misses are suggested for review and never merged automatically.

Model choice: pinned GPT-4.1 for prose and GPT-4.1-mini for chart reading, at temperature 0 with a content-addressed cache. Diagnostics record actual model calls, tokens, cache hits and stage timings; repairs can change usage. PDFs use PyMuPDF, with no model download. With no key, finance, selections, compliance and structure still run; prose falls back to attributed excerpts and unavailable chart readings block approval.

With more time: deterministic chart measurement to cross-check the vision readings, authenticated multi-user approval, and more cross-client fixtures. I left out Docker and a database because they add setup without improving correctness here.

## Where SPEC.md and the prior PMR disagree

The prior PMR's "Of which funded $391.8M" is the flash's commitment amount, not the funded amount, so this report labels it "Flash commitment total". The prior market update ranks the portfolio's return against the market index, which SPEC section 1.10 says not to conflate, so this report keeps them separate. The prior attribution table omits the second-largest position, and this one includes every role. The prior PMR says Vectera was retained in 2001, while the flash's inception data is older. I carried the sentence forward as source text rather than resolving it.
