# Vectera PMR Generator: Write-up

## Where the model stops and code starts

The rule I followed: if a step decides a number, a ranking, a filter or a pass/fail result, it is Python. If it needs reading or writing judgment, it is a model, and code checks the model's output before it reaches the report.

Code does all of the following: discovering and classifying input files, reading the flash by labels and headers, footing every fund, sleeve and portfolio total to the cent, computing dollar attribution (income + appreciation - fees), ranking the top two contributors, detractors and positions, applying the four IC-log filters with withdrawals and lapses, computing open approvals and the committed-or-approved totals, parsing guideline limits from the prior PMR, running the four compliance checks, and computing the direction of the office cap-rate gap. Every role and figure sentence in the report is a code template.

A model does two jobs. First, it reads the outlook deck's chart images, because those numbers exist only in pixels. Each reading is checked against the chart's axis range, keeps its slide locator, and must be confirmed by a human before approval. Second, it writes the connecting prose for featured funds, new commitments and the market update. The model never sees a raw number: every number in the source passages is replaced by a placeholder, each sentence must cite a registered passage, and code inserts the exact source strings back and rejects any sentence that adds, drops or moves a number. A second model pass checks each sentence against its quote for unsupported claims. If the prose fails, the report shows the attributed source excerpt instead. It never shows trimmed text.

## How I know the output is correct

The 123 tests include golden assertions for this quarter: the four featured funds and their roles, $456.8M committed or approved across 14 positions, the two new commitments led by Northgate, the Alder Creek withdrawal and Sentinel lapse, and the four compliance actuals. These are test fixtures only. Nothing in the pipeline expects these names or counts. Perturbation tests then change the inputs and check that the system adapts or refuses: shuffled and moved rows, renamed files, an added zero-balance fund, a one-cent cash error, an unknown IC action, conflicting IC amounts, a fund missing from one sheet, a manager report with a renamed heading or a word numeral, fabricated quotes, and tampered approvals.

At runtime, 58 reconciliation checks run on every report, and any currency mismatch is a blocker. For repeatability, a script runs the pipeline twice in separate processes with empty caches and compares every figure, chart reading, fund selection, order, role, compliance result and section. Two no-key runs and two live runs both passed. Live prose wording can differ between fresh runs, while a rerun with the cache produces identical prose. A regression shows up as a failing golden test, a perturbation that stops being caught, or a repeatability difference, and CI runs on Windows and macOS.

## Human review, warnings and blockers

The review page shows the draft next to its evidence. Clicking any paragraph, table or chart opens the source file and sheet/cell, page or slide, plus every input to the calculation. The reviewer confirms or corrects each chart reading (a correction needs a reason), reads the warnings, enters a name and approves. Approval is refused while blockers remain or if the draft, inputs or rendered exhibits changed since generation, and it produces a final PDF and a hash-bound approval record.

A warning means the draft is safe to read but a person should look. Examples: Meridian has no manager report, so its commentary is limited to flash figures; a manager report matched no fund, with suggested candidates; a paraphrase needs a meaning check. A blocker means a required figure cannot be trusted. Examples: any reconciliation failure, a fund missing from a flash sheet, an unparseable or ambiguous IC amount, an unknown committee action, a missing guideline in the prior PMR, an ambiguous required source, or chart values that could not be read. Blockers still produce a draft so the reviewer can see the problem.

## Next quarter and format changes

Next quarter, drop the new package into the inputs folder and run with the new client code and quarter. Nothing client- or quarter-specific is in the code. The client's full name and benchmark come from the flash. Guideline limits, the allocation policy, managers and disclosures come from the prior PMR. The IC logs are found by their columns, across years, so an approval made last year and still open is counted. Rows, fund counts and filenames can change because everything is located by labels and headers. A rehearsal script builds a different client for 1Q26, with renamed files, moved rows, one fund removed and two added, and an approval carried from a 2025 log into a 2026 withdrawal. It runs end to end without code changes.

For format changes, the section order and typography are read from the prior PMR's contents page and fonts. If the prior report gains a section the system does not know, it flags it rather than guessing. Section text is template code in one module, so a wording or layout change is a small, local edit. A new financial measure would need new code, and I would rather say so than pretend otherwise.

## Briefly

Architecture: a single pipeline (discover, compute, gather evidence, write, render), with one shared evidence ledger that every figure and sentence registers in. A small local browser workspace sits on top for analysts, and the CLI does the same thing without it.

Traceability: manifest.json lists every report block with its resolved evidence and source locators (file plus sheet/cell, page or slide), and evidence.json holds every fact, formula and input.

Ambiguity and entity resolution: names are matched by explicit, logged rules for legal suffixes, punctuation, Roman, Arabic and word numerals, "&" and a few abbreviations. Near misses are suggested for review and never merged automatically.

Model choice: GPT-4.1 for prose and GPT-4.1-mini for chart reading, at temperature 0 with a content-addressed cache. A cold run takes about a minute, makes 19 calls and costs under $0.10. PDFs are read with PyMuPDF, which is fast and needs no model download. With no key, all figures, selections, compliance and structure are still produced. Narrative falls back to source excerpts, and chart values are unavailable and block approval.

With more time: deterministic chart measurement to cross-check the vision readings, authenticated multi-user approval, and more cross-client fixtures. I left out Docker and a database because they add setup without improving correctness here.

## Where SPEC.md and the prior PMR disagree

The prior PMR's "Of which funded $391.8M" is the flash's commitment amount, not the funded amount, so this report labels it "Flash commitment total". The prior market update ranks the portfolio's return against the market index, which SPEC section 1.10 says not to conflate, so this report keeps them separate. The prior attribution table omits the second-largest position, and this one includes every role. The prior PMR says Vectera was retained in 2001, while the flash's inception data is older. I carried the sentence forward as source text rather than resolving it.
