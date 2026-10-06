# Vectera PMR Generator

## Round-Two Submission

This branch contains the optional v2, based on the unchanged `v1-submission` tag.
Start with [the round-two delivery guide](round2/README.md) for the one-page note, original v1 failure,
1Q26 draft, and verification records. The 1Q26 report is a **blocked draft**, not an approved final report.
The original 4Q25 submission below remains as the comparison baseline.

Generates a client's quarterly Performance Measurement Report (PMR) from a folder of quarterly inputs.
The only inputs are a **client code** and a **quarter**, for example `CPERS` and `4Q25`. The system finds the
right files itself, computes every figure in code, writes the narrative with a model under strict checks,
and stops at a human review step before anything is final.

**Included in this repository:** [4Q25 draft PMR](output/CPERS_PMR_4Q25_DRAFT.pdf),
[two-page write-up](output/writeup.pdf), tests, source documents and
[audit manifest](output/manifest.json). The report is marked DRAFT until a human reviews and approves it.

## Get Started on Windows 11

Requires **Python 3.12**, including the Windows Python launcher (`py`). First-time setup needs internet
access. No Docker, database, Git installation or manual dependency setup is needed.

1. On GitHub, select **Code > Download ZIP** and extract it to a normal, writable folder. Alternatively, clone the repository if you already use Git.
2. Install Python 3.12 if needed. Open PowerShell and run `py -3.12 --version` to check it is available.
3. Open PowerShell in the extracted project folder, where `start.cmd` and `README.md` are located.
4. Add an OpenAI API key as described below, unless your environment already has one.
5. Start the application:

```powershell
.\start.cmd
```

The launcher creates `.launcher-venv`, installs the pinned dependencies and opens the local browser
workspace. It prints the exact localhost URL; the port is chosen automatically. Keep the terminal open
while using the app. Press Ctrl+C in that terminal to stop it.

In the app, enter **CPERS** and **4Q25**, leave the supplied inputs folder selected, and click
**Generate Report**. Open the new run to inspect its report, charts and warnings. Generation produces
`CPERS_PMR_4Q25_DRAFT.pdf`; human approval produces `CPERS_PMR_4Q25.pdf`.

For a different package, use **Choose Folder** or enter its local folder path. Then enter that package's
client code and quarter. The package needs the flash, prior PMR, market deck, IC logs and allocation
history, plus any available manager reports. Missing manager evidence is flagged, not invented.

## Add an API Key

**OpenAI is recommended for this submission. Only one provider key is needed.** The submitted report
and primary live checks used OpenAI. Anthropic was also tested, but Sonnet 4.6 misclassified one
unlabeled chart as having printed value labels; OpenAI kept its readings marked approximate.

If `OPENAI_API_KEY` is already set in your environment, skip this step. Existing environment variables
take priority over `.env`, so evaluator-provided keys work without editing any file.

Otherwise, run these commands in the project folder before starting the application:

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace the empty value with your own key, then save and close Notepad:

```dotenv
OPENAI_API_KEY="paste-your-openai-key-here"
```

Do not overwrite an existing `.env`; edit it instead. The file is ignored by Git and excluded from
submission ZIPs. The app sends source passages and chart images to the selected provider's API; the key
is not embedded in the report or browser page. Restart the app after changing a key.

With both keys set, **OpenAI takes priority**. Its defaults are `gpt-4.1-2025-04-14` for prose and
`gpt-4.1-mini-2025-04-14` for charts. Optional `PMR_MODEL` and `PMR_VISION_MODEL` variables override them.
To use Anthropic instead, remove or empty `OPENAI_API_KEY` in both the environment and `.env`, then set
`ANTHROPIC_API_KEY` to a workspace-scoped key. Its default is `claude-sonnet-4-6` for both jobs.
Cross-workspace Anthropic keys requiring a workspace-ID header are not supported.

**Without a key:** the app still generates the financial figures, fund selection, compliance and report
structure. Prose falls back to attributed source excerpts. Image-only chart values remain unavailable,
so the draft cannot be approved. A key is needed for the complete workflow. API usage and cache hits are
recorded in `output/diagnostics.json`; cost and run time depend on the model and any repair calls.

## macOS / Linux and Command Line

From the project folder, add a key to `.env` using `.env.example` as the template, then launch:

```bash
python3.12 scripts/launch.py
```

For a command-line-only run on Windows, without the launcher:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pmr generate --client CPERS --quarter 4Q25
.\.venv\Scripts\python.exe -m pmr review
```

The review command serves `http://127.0.0.1:8765/review.html`. On macOS/Linux, use
`python3.12 -m venv .venv` and `.venv/bin/python` in place of the Windows Python commands.
Optional generation flags are `--inputs <folder>` and `--output <folder>` (defaults: `inputs`, `output`).
Use the new client and quarter for unseen inputs; no code edits are needed.

## Report Presentation

**Report presentation.** The cover, headings, typography, emphasis and vector charts follow the prior PMR.
The portrait appendix preserves every supplied flash column and blank cell, rather than copying the prior
quarter's smaller selection of columns. Wide return exhibits are split by horizon with one header row;
`TGRS/TNET` are displayed as `GRS/NET`, and market-value share as `% NAV`. Currency signs and accounting
negatives are presentation only: source strings and exact locators remain in the manifest. A compact net
annual-return summary accompanies the full annual-return exhibits.

Source-excerpt fallbacks preserve the writer's complete numerical inventory, including dated market
risks and scoped source bindings. A fresh-run test caught and fixed an earlier fallback that omitted
those dates; meaning checks still fail when a value or its source context changes.

Unchanged reruns reuse a local cache of model responses.

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
4. Enter your reviewer name and acknowledge the PDF, sources, charts and warnings. **Approve & Download Final PDF** becomes available only when all requirements are met. Backend checks also enforce these requirements. Successful approval downloads the named final PDF; a download link remains available if your browser blocks it. If you corrected any chart, this first submission saves a **new draft**, not an approval. Select **Review corrected draft**, inspect the updated report, reconfirm charts and acknowledge it again. Changed market evidence invalidates the old prose; newly written prose receives the same number, quote and paraphrase checks, or verified observations replace it if synthesis is unavailable.
5. With no further corrections, approval writes `CPERS_PMR_4Q25.pdf` and a hash-bound `approval.json`. Names follow the requested client and quarter; drafts carry an `_DRAFT` suffix. Internal `report.pdf` and `final_report.pdf` copies remain for compatibility. Approval is refused if the draft JSON, displayed draft PDF, inputs, implementation or exhibits changed. The approval record includes the exact draft PDF hash as well as the final PDF hash.

Missing cash rows or blank holding NAVs do not erase known holdings or turn them into open approvals. Performance-dependent attribution requires complete cash data, and position ranking requires complete NAV data. Missing figures retain their cell locators and block release. Unresolved IC amounts make the committed-or-approved total unavailable, never a partial sum presented as complete.

## Verification

After starting once with `start.cmd`, use the launcher's Python environment in PowerShell:

```powershell
.\.launcher-venv\Scripts\python.exe -m pytest -q
.\.launcher-venv\Scripts\python.exe scripts/verify_repeatability.py --client CPERS --quarter 4Q25
.\.launcher-venv\Scripts\python.exe scripts/rehearse_unseen.py
```

These check the sample answers and guardrails, compare two separate no-key runs, and rehearse a different
client in 1Q26. They do not require paid model calls. On macOS/Linux, substitute `.launcher-venv/bin/python`.
If you used the manual setup, substitute `.venv\Scripts\python.exe` or `.venv/bin/python` instead.

For two fresh model-backed runs, add `--online --record output/live_repeatability.json` to the
repeatability command; this uses the configured key and incurs API charges. The optional
`scripts/package_submission.py` and `scripts/verify_clean_install.py` scripts build a secret-free ZIP
and test it in a fresh Python 3.12 environment. A ZIP is not needed to run the GitHub submission.

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
inputs/     the supplied 4Q25 package
output/     generated report, evidence and verification results
```
