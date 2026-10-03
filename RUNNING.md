# Vectera PMR Submission

The generator takes a client short code and reporting quarter, discovers relevant sources, calculates financial results, and produces a PDF plus an evidence review. It does not require manually selected filenames, transcribed facts, or code changes for another period.

## Quick start: Windows 11 / Python 3.12

From the extracted submission folder, run **one command** in PowerShell:

```powershell
.\start.cmd
```

The launcher creates an isolated environment, installs pinned dependencies on first use, and opens the local browser workspace. It picks an available local port automatically. Keep the terminal open; Ctrl+C stops the server and any active worker. First use requires Python 3.12 (with the Windows `py` launcher) and internet access for dependency installation. Subsequent launches reuse the environment unless `requirements.txt` changes. API keys come from existing environment variables or `.env`; no key produces a flagged draft, not a crash.

### Browser workflow

1. **New Report:** enter the client code and reporting quarter, for example `CPERS` / `4Q25`. The supplied `inputs` folder is selected by default.
2. **Source Documents:** optionally enter another local package folder or choose a folder to import. Imports preserve nested document folders and accept PDF, XLSX and PPTX, up to 100 documents / 25 MB. Larger packages can use a local path. A new quarter needs that quarter's actual source documents; changing the quarter field does not invent data.
3. **Generate Report:** the real pipeline stages show progress. One worker runs at a time. Each run has an isolated output folder and cache, so the sample and earlier drafts are not overwritten. Failures show the discovery/validation reason; private worker diagnostics stay in that run's `run.log`.
4. **Runs:** select a report. **Evidence Review** shows linked sources, blockers, warnings, chart confirmation and named approval. **PDF Preview** shows the formatted draft. Switching views preserves the review form unless another run is selected.
5. **Open PDF** and **Audit Bundle** download that run's report and machine-readable evidence. The bundle excludes API keys, provider caches and private logs. The submission ZIP is a separate code-and-documents deliverable.

The workspace is local-only, bound to `127.0.0.1`, with same-origin/host checks and a per-launch token for writes. Credentials are not sent to the browser. It is not an authenticated multi-user service. Restarting restores saved run history; interrupted runs are marked failed rather than silently resumed. Existing `output/report.pdf` is listed as **Existing draft**.

For a non-interactive demo:

```powershell
.\start.cmd --client CPERS --quarter 4Q25
```

On macOS/Linux the equivalent bootstrap command is `python3.12 scripts/launch.py`. Optional `--inputs`, `--output`, and `--no-browser` flags are forwarded to the application. There is no Docker prerequisite.

### Manual setup alternative

Run these commands from the extracted submission folder in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pmr generate --client CPERS --quarter 4Q25
.\.venv\Scripts\python.exe -m pmr review
```

Open http://127.0.0.1:8765/review.html. Stop the server with Ctrl+C.

On macOS/Linux, use `python3.12 -m venv .venv` and `.venv/bin/python` in place of the Windows Python path. No Docker, office installation, PDF converter, local LLM, or external OCR executable is required.

The `README.md` and `SPEC.md` in this folder are the original assignment documents. This file contains submission run instructions.

## Model access

For local use, open `.env` in the project folder and paste your OpenAI key between the quotes on `OPENAI_API_KEY=""`. The CLI loads this file automatically. Only one provider key is needed; Anthropic is optional. A safe `.env.example` is included in the submission, but the actual `.env` is excluded from Git and the submission ZIP. Existing environment variables take precedence over the file.

Set a key in the same terminal before starting generation:

```powershell
$env:OPENAI_API_KEY = "your-key"
# Alternatively:
$env:ANTHROPIC_API_KEY = "your-key"
```

On macOS/Linux, use `export OPENAI_API_KEY="your-key"`. Do not commit keys. The application does not print or write them. If both keys are set, OpenAI is selected. OpenAI defaults to `gpt-4.1-2025-04-14` for evidence investigation and prose, and `gpt-4.1-mini-2025-04-14` for chart vision, evaluated separately. Anthropic defaults to `claude-sonnet-4-6`. `PMR_MODEL` and `PMR_VISION_MODEL` override the respective model identifiers for the selected provider.

With no key, the generator still creates all required sections, verified portfolio figures, rankings, compliance checks, charts derived from workbooks, source excerpts, and the flash appendix. Market chart-image numbers remain unavailable, with their original images visible in review. This is a usable financial draft, not an approved final report. Failed model access follows the same conservative degradation path.

The current draft was generated with live OpenAI access. All seven chart images were automatically extracted, including approximate gridline readings where labels are absent. Two independent live runs passed the full semantic repeatability check. Human chart confirmation/final approval and an observed Windows 11 interactive run remain separate completion gates.

Requests have a 45-second timeout and a ten-minute total model-time budget. Exhausting the budget retains the financial draft and flags unavailable enrichment. `verification.json` records API call counts and returned provider token usage; billed account charges have not been queried.

## Another client or period

Place the new package in `inputs/`, then change only the two run parameters:

```powershell
.\.venv\Scripts\python.exe -m pmr generate --client CLIENTCODE --quarter 1Q26
```

To use another input folder, supply `--inputs C:\path\to\inputs`. To keep several runs, supply `--output output\CLIENTCODE_1Q26`. Folder paths are optional environment settings; client and quarter are the only required report inputs.

The workbook contract is label-driven: sheet names and column meanings remain consistent; rows, fund counts, and filenames may change. The prior report supplies client policy and reusable formatting. A missing required source produces an explicit blocker or `failure.json`, rather than a guessed number.

## Review, correct, approve

1. Inspect the PDF and verification summary. Click report paragraphs, tables, or charts in the review page to inspect source locators and calculation inputs.
2. Inspect every house-view chart image. Its extraction appears beside the original image. Values marked `~` are approximate gridline readings, not exact underlying data. Correct the JSON if needed, supply a reason, then confirm it. A correction modifies an existing automatic extraction; it cannot substitute for absent initial extraction.
3. Read the warnings. Missing manager commentary is a warning; financial reconciliation failures, missing policy, ambiguous required sources, and unavailable image extraction block finalization.
4. Enter your reviewer name, acknowledge review, and approve. The backend checks draft/source/exhibit hashes, every chart confirmation and unresolved blockers. It produces `final_report.pdf`, `approval.json`, `final_evidence.json`, `final_sections.json`, `final_manifest.json`, and `final_semantic_manifest.json`. Regenerating a draft invalidates old approved artifacts.

Financial corrections belong in the authoritative workbook, followed by regeneration and review. Model sentences carry verified source quotes and host-owned numerical placeholders; financial calculations remain code-generated. A separate model check rejects unsupported meaning, but it is not an entailment guarantee: human review remains required. Chart corrections rebind numeric slots; changes invalidating a conclusion require regeneration. This prototype does not offer arbitrary financial or narrative overrides.

## Output files

| File | Purpose |
|---|---|
| `output/report.pdf` | Current draft PMR |
| `output/review.html` | Local evidence review; readable without a server, approval requires the server |
| `output/evidence.json` | Every extracted fact, source locator, formula, matching decision, and check |
| `output/draft.json` | Complete report model, claim-to-evidence references, input hashes, draft hash |
| `output/verification.json` | Financial checks, rankings, issues, source hashes and meaningful-output hash |
| `output/manifest.json` | Report claims and scoped evidence paths; attribution has cell-level references |
| `output/semantic_manifest.json` | Canonical figures, charts, selection, roles, compliance and structure |
| `output/agent_trace.json` | Read-only tool actions, observations, quote validation and stopping reason |
| `output/diagnostics.json` | Stage timings, API usage, cache statistics and issue counts |
| `output/review.md` | Exported WARNING/BLOCKER/REVIEW queue |
| `output/live_repeatability.json` | Independent live API runs with empty caches |
| `output/unseen_rehearsal.json` | Different-client 1Q26 full-pipeline fixture results |
| `output/regression_matrix.json` | Observed test outcomes, including expected rejection cases |
| `output/assets/` | Extracted deck images and workbook charts |
| `output/cache/` | Content-addressed model responses; never API keys |
| `output/appendix.pdf` | Unmodified supplied flash PDF |

The standalone `appendix.pdf` retains the six original source pages. Every report page is portrait US Letter. PyMuPDF extracts the source tables, which are retypeset with one header row, external titles and source-page captions. Grouped return headers become single period/metric labels; adjacent horizons share readable tables. Empty spreadsheet padding and nonnumerical section-only rows are removed, but all displayed financial values and blank data cells are retained. The sample is 15 pages; pagination can grow for larger unseen portfolios. Market Update uses source-backed prose rather than seven separate tables; full chart observations remain in the evidence manifests.

An unfamiliar appendix layout is retained as the original vector exhibit on portrait pages if its text remains readable at 7pt or above. Its original header styling is not rewritten. If it cannot fit readably, generation stops with an explicit adapter/review requirement rather than guessing columns or dropping values.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\verify_repeatability.py --client CPERS --quarter 4Q25
.\.venv\Scripts\python.exe scripts\verify_repeatability.py --client CPERS --quarter 4Q25 --online --record output\live_repeatability.json
.\.venv\Scripts\python.exe scripts\rehearse_unseen.py
```

The repeatability command launches separate processes with empty output folders and caches. It fails on any canonical difference in financial figures, chart observations, fund selection/order/roles, compliance or structure, or on an implementation revision difference. By default it removes keys; `--online` retains them for independent API runs. Full payload equality, including prose and extraction metadata, is recorded separately: the final live pair matched canonically, not in its entire payload. Passing twice is observed evidence, not a universal promise of provider determinism. A pinned snapshot, temperature zero, seed and a source/prompt/image-bound cache help stability; chart review remains essential.

Money uses Decimal, serialized as base-ten strings. Active-portfolio currency reconciliations have zero tolerance: a one-cent error blocks approval. Rounded supporting-document statistics have separately declared precision, not a tolerance on the flash. Percentage sums permit their explicitly recorded source precision. The realized-only source discrepancy is a warning because that row is outside the active portfolio. Tests cover bad numbers, altered rows/names/counts/client/period, multi-year logs, agent feedback and limits, chart schema errors, missing keys, tampering and unsupported quotes.

Direct dependencies are pinned in `requirements.txt`. Development used Python 3.12 on macOS. A Windows CI workflow is included; its result must be observed on a hosted runner before treating Windows support as verified.

## Architecture and code guide

| Module | Responsibility |
|---|---|
| `ingest.py` | Content discovery, quarter parsing, workbook header/cell access, conservative entity normalization |
| `finance.py` | Financial formulas, attribution roles, committee event state, policy extraction, compliance |
| `evidence.py` | Stable fact identifiers, formulas, source locators, checks and issues |
| `models.py` | Approved API adapters, shared time budget, response caching and usage counters |
| `agent.py` | Model-directed read-only action/observation loop over registered source passages |
| `numeric.py` | Exact currency validation, serialization restoration and display rounding |
| `charts.py` | Shared extraction/correction schema, units, bounds and uncertainty |
| `market.py` | Deterministic selection of current, portfolio-relevant market observations |
| `crosschecks.py` | Precision-aware supporting-source checks and deterministic cap-rate gap direction |
| `verification.py` | Claim manifest and full meaning-bearing reproducibility signature |
| `narrative.py` | Manager passages, deck text/images, model image extraction, allocation history |
| `synthesis.py` | Scoped quotes, exact numeric placeholders, bounded repair and complete-source fallback |
| `template.py` | Prior PDF typography, primary color and contents order |
| `report.py` | Shared report model, charts and PDF layout |
| `appendix.py` | Parsed source tables retypeset on portrait Letter with single-row headers |
| `review.py` | Evidence UI, chart corrections, approval record and local server |
| `pipeline.py` | Run orchestration and output manifests |

Module docstrings describe ownership. Comments explain important financial, source-precedence, and approval decisions. See `docs/WALKTHROUGH.md` for a short live-demo script and `docs/WRITEUP.md` for the submission rationale.

The evidence agent chooses what to inspect and validates verbatim passages. Its validated quotes feed synthesis: the matching narrative must cite its focus evidence. Each sentence names a source; the host attaches its exact quote, with verbatim validation for any model-supplied narrower quote. Numeric values become placeholders; Python restores exact source strings and rejects raw numbers, changed signs/units, wrong source scope or missing/duplicated slots. Sentence ordering may change, but the numerical inventory cannot. This preserves occupancy figures and numerical asset names without model transcription or arithmetic. Unknown headings retain page evidence and a warning. Unmatched reports receive review suggestions, not false absence claims. Rejected prose is labelled pending review with full source excerpts. See `docs/ARCHITECTURE.md` for trust boundaries.

Input hashes are captured before extraction and checked again before the draft is saved. A source edited during an API call invalidates the run rather than binding old calculations to a new file. The implementation revision is also recorded and checked.

## Package

After review and approval, run `python scripts/package_submission.py --final`. Final mode refuses missing approval artifacts or a modified approved PDF. Without `--final` it packages a clearly labeled draft for inspection. Both exclude keys, environments, caches and personal study material. No command in the application publishes to GitHub.

Official API references: [OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-4.1), [Anthropic model documentation](https://platform.claude.com/docs/en/models/sonnet-4-6/overview).
