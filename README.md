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

Open the review page, click any paragraph, table or chart to see its source locators and calculation
inputs, confirm or correct each chart-image reading (a correction needs a reason), then enter your name and
approve. Approval is refused while any blocker remains or if the draft, inputs or exhibits changed since
generation. It writes `final_report.pdf` and a hash-bound `approval.json`.

## Verification

```powershell
python -m pytest -q                                                        # 126 tests: golden 4Q25 answers, perturbations, guardrails
python scripts/verify_repeatability.py --client CPERS --quarter 4Q25       # two clean no-key runs must match
python scripts/verify_repeatability.py --client CPERS --quarter 4Q25 --online --record output/live_repeatability.json
python scripts/rehearse_unseen.py                                          # different client, 1Q26, changed rows and funds
```

Results from the submitted run are in `output/test-results.xml`, `output/regression_matrix.json`,
`output/repeatability.json`, `output/live_repeatability.json` and `output/unseen_rehearsal.json`.
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
