# Vectera PMR Submission

The generator takes a client short code and reporting quarter, discovers relevant sources, calculates financial results, and produces a PDF plus an evidence review. It does not require manually selected filenames, transcribed facts, or code changes for another period.

## Quick start: Windows 11 / Python 3.12

From the extracted submission folder, run **one command** in PowerShell:

```powershell
.\start.cmd
```

Enter the client code and reporting quarter when prompted. The launcher creates an isolated environment, installs pinned dependencies on first use, generates the draft, and opens the evidence review in your default browser. It picks an available local port automatically. Keep the terminal open during review; Ctrl+C stops the server. First use requires Python 3.12 (with the Windows `py` launcher) and internet access for dependency installation. Subsequent launches reuse the environment unless `requirements.txt` changes. API keys come from existing environment variables or `.env`; no key produces a flagged draft, not a crash.

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

On macOS/Linux, use `export OPENAI_API_KEY="your-key"`. Do not commit keys. The application does not print or write them. If both keys are set, OpenAI is selected. The defaults are `gpt-4.1-mini-2025-04-14` and `claude-sonnet-4-6`; `PMR_MODEL` can override the model identifier for the selected provider.

With no key, the generator still creates all required sections, verified portfolio figures, rankings, compliance checks, charts derived from workbooks, source excerpts, and the flash appendix. Market chart-image numbers remain unavailable, with their original images visible in review. This is a usable financial draft, not an approved final report. Failed model access follows the same conservative degradation path.

The checked-in report was generated in **no-key mode**. Live API extraction and actual Windows execution require separate verification before claiming they have been tested.

Requests have a 45-second timeout and a ten-minute total model-time budget. Exhausting the budget retains the financial draft and flags unavailable enrichment. `verification.json` records API call counts and provider token usage; actual API cost has not been measured in this no-key development run.

## Another client or period

Place the new package in `inputs/`, then change only the two run parameters:

```powershell
.\.venv\Scripts\python.exe -m pmr generate --client CLIENTCODE --quarter 1Q26
```

To use another input folder, supply `--inputs C:\path\to\inputs`. To keep several runs, supply `--output output\CLIENTCODE_1Q26`. Folder paths are optional environment settings; client and quarter are the only required report inputs.

The workbook contract is label-driven: sheet names and column meanings remain consistent; rows, fund counts, and filenames may change. The prior report supplies client policy and reusable formatting. A missing required source produces an explicit blocker or `failure.json`, rather than a guessed number.

## Review, correct, approve

1. Inspect the PDF and verification summary. Click report paragraphs, tables, or charts in the review page to inspect source locators and calculation inputs.
2. Inspect all seven house-view chart images. With model access, their extracted data is shown beside the image. Correct the extraction JSON if needed, then confirm it. A correction modifies an existing automatic extraction; it cannot substitute for an absent initial extraction.
3. Read the warnings. Missing manager commentary is a warning; financial reconciliation failures, missing policy, ambiguous required sources, and unavailable image extraction block finalization.
4. Enter the reviewer name, acknowledge review, and approve. Approval verifies the draft hash and unchanged source files, requires all chart confirmations, and generates `final_report.pdf`, `approval.json`, `final_evidence.json`, and `final_sections.json`.

Financial corrections belong in the authoritative input workbook, followed by regeneration and renewed review. Manager narrative is limited to verified source quotations; edit a source or remove an unsupported claim and rerun rather than adding unaudited prose. This prototype does not offer arbitrary financial or narrative overrides in the browser.

## Output files

| File | Purpose |
|---|---|
| `output/report.pdf` | Current draft PMR |
| `output/review.html` | Local evidence review; readable without a server, approval requires the server |
| `output/evidence.json` | Every extracted fact, source locator, formula, matching decision, and check |
| `output/draft.json` | Complete report model, claim-to-evidence references, input hashes, draft hash |
| `output/verification.json` | Financial checks, rankings, issues, source hashes and meaningful-output hash |
| `output/assets/` | Extracted deck images and workbook charts |
| `output/cache/` | Content-addressed model responses; never API keys |
| `output/appendix.pdf` | Unmodified supplied flash PDF |

The appendix retains the supplied six pages. This makes the no-key report 17 pages, compared with the example's 13 pages and its shorter appendix. Financial tables remain readable rather than being compressed to meet an approximate page count.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\verify_repeatability.py --client CPERS --quarter 4Q25
```

The repeatability command launches separate Python processes with empty output folders and caches. By default it removes model keys. It compares financial values, roles, compliance and structure using a financial hash, and separately records whether the full report model agrees. `--online` retains keys for independent API runs; extractive sentence selection and image readings can differ and still require human review.

Financial checks include per-fund cash roll-forward, cross-sheet NAV, sleeve and portfolio footing, commitments, and diversification totals. Money checks allow two cents for displayed source rounding; exact deltas are retained, not silently overwritten. Tests cover changed row positions, filenames, fund count, client identity, policy, log order, future approvals, missing keys, tampered drafts, failed model calls, and unverifiable model quotations.

Direct dependencies are pinned in `requirements.txt`. Development used Python 3.12 on macOS. A Windows CI workflow is included; its result must be observed on a hosted runner before treating Windows support as verified.

## Architecture and code guide

| Module | Responsibility |
|---|---|
| `ingest.py` | Content discovery, quarter parsing, workbook header/cell access, conservative entity normalization |
| `finance.py` | Financial formulas, attribution roles, committee event state, policy extraction, compliance |
| `evidence.py` | Stable fact identifiers, formulas, source locators, checks and issues |
| `models.py` | Approved API adapters, bounded requests, response caching and verified quote selection |
| `narrative.py` | Manager passages, deck text/images, model image extraction, allocation history |
| `template.py` | Prior PDF typography, primary color and contents order |
| `report.py` | Shared report model, charts and PDF layout |
| `review.py` | Evidence UI, chart corrections, approval record and local server |
| `pipeline.py` | Run orchestration and output manifests |

Module docstrings describe ownership. Comments explain important financial, source-precedence, and approval decisions. See `docs/WALKTHROUGH.md` for a short live-demo script and `docs/WRITEUP.md` for the submission rationale.

Official API references: [OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-4.1-mini), [Anthropic model documentation](https://platform.claude.com/docs/en/models/sonnet-4-6/overview).
