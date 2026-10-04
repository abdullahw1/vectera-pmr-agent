# Vectera PMR Generator

Generates a client's quarterly Performance Measurement Report (PMR) from a folder of quarterly inputs.
The only inputs are a **client code** and a **quarter**, for example `CPERS` and `4Q25`. The system finds the
right files itself, computes every figure in code, writes the narrative with a model under strict checks,
and stops at a human review step before anything is final.

**Submitted outputs:** `output/report.pdf` (the 4Q25 draft), `output/writeup.pdf` (two-page rationale),
`output/review.html` (evidence review), and `output/manifest.json` (every claim mapped to its source).

## Run it

Requires Python 3.12. First-time setup needs internet access to install the pinned dependencies.

**Windows (one command):**

```powershell
.\start.cmd
```

This creates a private environment, installs `requirements.txt`, and opens the local browser workspace:
enter the client and quarter, select **Generate Report**, then review and approve the draft.
On macOS/Linux, run `python3.12 scripts/launch.py` instead.

**Command line (no browser):**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pmr generate --client CPERS --quarter 4Q25
.\.venv\Scripts\python.exe -m pmr review      # serves the evidence review at http://127.0.0.1:8765/review.html
```

Optional flags: `--inputs <folder>` (default `inputs`) and `--output <folder>` (default `output`).
For another period or client, change only the two parameters, for example `--client NWPT --quarter 1Q26`.

**API keys.** Read from `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, or from a local `.env` (see `.env.example`).
If both are set, OpenAI is used: `gpt-4.1-2025-04-14` writes prose and `gpt-4.1-mini-2025-04-14` reads chart
images. Anthropic uses `claude-sonnet-4-6`. `PMR_MODEL` and `PMR_VISION_MODEL` override these.
**With no key the run still completes:** every figure, fund selection, role, compliance result and section is
produced by code. Fund and market narrative fall back to attributed source excerpts, and the deck's chart
values are marked unavailable. That is a blocker, so a no-key draft cannot be approved.

**Report presentation.** The cover, headings, typography, emphasis and vector charts follow the prior PMR.
The portrait appendix preserves every supplied flash column and blank cell, rather than copying the prior
quarter's smaller selection of columns. Wide return exhibits are split by horizon with one header row;
`TGRS/TNET` are displayed as `GRS/NET`, and market-value share as `% NAV`. Currency signs and accounting
negatives are presentation only: source strings and exact locators remain in the manifest. A compact net
annual-return summary accompanies the full annual-return exhibits.

Source-excerpt fallbacks preserve the writer's complete numerical inventory, including dated market
risks and scoped source bindings. A fresh-run test caught and fixed an earlier fallback that omitted
those dates; meaning checks still fail when a value or its source context changes.

A cold run with a key takes about a minute and makes about 19 API calls (under $0.10). Reruns reuse a
content-addressed cache.

## What happens in a run

1. **Discover** (`ingest.py`): classifies every file by its *content*, not its name, and records why each
   file was accepted or ignored. Decoy flashes for other quarters or clients are rejected this way.
2. **Compute** (`finance.py`): reads the flash by row labels and column headers, never cell coordinates.
   It foots funds → sleeves → portfolio to the cent, ranks contributors, detractors and positions in dollars,
   applies the four IC-log filters plus withdrawals and lapses, and runs the four compliance checks. Guideline
   limits are parsed from the prior PMR, not hardcoded.
3. **Gather evidence** (`narrative.py`, `crosschecks.py`): matches manager reports to funds with explicit
   normalisation rules (legal suffixes, Roman, Arabic and word numerals, "&"). Unmatched reports are flagged
   with suggestions and never merged silently. Commentary is read as heading-plus-paragraph sections and chosen
   by what the heading is about (drivers, then strategy, then status), so a renamed heading still works. Deck chart values are read by a vision model, then checked
   against the axis range.
4. **Write** (`synthesis.py`): the model sees source passages with every number replaced by a placeholder.
   Each sentence must cite a registered passage, and code puts the exact source numbers back. A second model
   pass checks each sentence against its quote. Anything that fails falls back to the attributed source text.
5. **Render and record** (`report.py`, `verification.py`, `review.py`): a PDF in the prior PMR's style, a
   claim manifest, an evidence ledger, and a review queue that separates **warnings** (draft can proceed)
   from **blockers** (cannot be finalised).

## Review and approve

1. Open **Report**, inspect the draft PDF, and click paragraphs or table cells for readable source locators and calculation inputs. Audit JSON is available under **Audit details**.
2. Open **Charts**. Compare each extraction with the displayed source image. Edit individual values if needed, add a correction reason, and select **Confirm These Chart Values**. **Previous chart** and **Next chart** retain value edits in this session. Reloading deliberately requires a new review.
3. Open **Issues**. Blockers require corrected inputs and regeneration; warnings require inspection but do not prevent release. Chart confirmations are shown separately.
4. Enter your reviewer name and acknowledge the PDF, sources, charts and warnings. **Approve & Create Final PDF** becomes available only when all requirements are met. Backend checks also enforce these requirements. If you corrected any chart, this first submission saves a **new draft**, not an approval. Select **Reload corrected draft**, inspect the updated report, reconfirm charts and acknowledge it again. Changed market evidence invalidates the old prose; newly written prose receives the same number, quote and paraphrase checks, or verified observations replace it if synthesis is unavailable.
5. With no further corrections, approval writes `final_report.pdf` and a hash-bound `approval.json`. It is refused if the draft JSON, displayed draft PDF, inputs, implementation or exhibits changed. The approval record includes the exact draft PDF hash as well as the final PDF hash.

Missing cash rows or blank holding NAVs do not erase known holdings or turn them into open approvals. Performance-dependent attribution requires complete cash data, and position ranking requires complete NAV data. Missing figures retain their cell locators and block release. Unresolved IC amounts make the committed-or-approved total unavailable, never a partial sum presented as complete.

## Verification

```powershell
python -m pytest -q                                                        # golden 4Q25 answers, perturbations, guardrails
python scripts/verify_repeatability.py --client CPERS --quarter 4Q25       # two clean no-key runs must match
python scripts/verify_repeatability.py --client CPERS --quarter 4Q25 --online --record output/live_repeatability.json
python scripts/rehearse_unseen.py                                          # different client, 1Q26, changed rows and funds
python scripts/package_submission.py                                      # builds a draft package without secrets
python scripts/verify_clean_install.py                                     # Python 3.12; fresh venv, full tests, no-key run
```

Results from the submitted run are in `output/test-results.xml`, `output/regression_matrix.json`,
`output/repeatability.json`, `output/live_repeatability.json`, `output/unseen_rehearsal.json` and
`output/clean_install_verification.json`. Browser checks are recorded in `output/review_ui_verification.json`; their approval request is mocked, never a real release. The clean-install record names the tested host; it does not claim Windows validation on macOS.
CI (`.github/workflows/verify.yml`) runs the tests and the repeatability check on Windows and macOS.

## Layout

```
pmr/        pipeline code (entry point: python -m pmr)
pmr/web/    browser workspace and review page
tests/      pytest suite
scripts/    launcher, repeatability, unseen-input rehearsal, packaging
docs/       WRITEUP.md (source of output/writeup.pdf)
inputs/     the supplied 4Q25 package
output/     generated report, evidence and verification results
```
