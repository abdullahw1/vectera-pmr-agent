# Vectera PMR Agent

Generates a quarterly Performance Measurement Report from spreadsheets, manager reports, a market deck and an IC log. Enter a client and quarter; the app finds the sources, checks the figures and creates a draft for review.

[View the CPERS 1Q26 draft](submission/CPERS_PMR_1Q26_DRAFT.pdf), [v1 result](submission/v1-failure.json) or [audit bundle](submission/audit.zip). The received 1Q26 sources are in `inputs/`; original 4Q25 sources are in `fixtures/4Q25/`. Neither package has been edited.

## Start

Install **Python 3.12**. Download this branch from **Code > Download ZIP**, extract it and open a terminal in the folder containing `start.cmd`.

**Windows 11 / PowerShell:**

```powershell
py -3.12 --version
.\start.cmd --client CPERS --quarter 1Q26
```

**macOS / Linux:**

```bash
python3.12 scripts/launch.py --client CPERS --quarter 1Q26
```

The launcher installs the pinned dependencies and opens the local browser app. First setup needs internet access. Keep the terminal open; Ctrl+C stops the server. No database or Docker is needed.

## API Key

**OpenAI is preferred; one provider key is enough.** Evaluator-supplied environment variables work directly. For local use, copy `.env.example` to `.env` and add your key:

```powershell
Copy-Item .env.example .env
notepad .env
```

```dotenv
OPENAI_API_KEY="your-key-here"
```

Do not overwrite an existing `.env`. It is ignored by Git. Restart after changing keys. The model receives source passages and chart images.

OpenAI takes priority when both keys are present. Defaults: `gpt-4.1-2025-04-14` for prose and `gpt-4.1-mini-2025-04-14` for charts. `PMR_MODEL` and `PMR_VISION_MODEL` override them. Anthropic is supported through `ANTHROPIC_API_KEY`, defaulting to `claude-sonnet-4-6`; unset the OpenAI key to select it. Keys requiring an Anthropic workspace-ID header are not supported.

Without a key, calculations and draft generation still work. Commentary uses source excerpts; image-only chart readings remain unavailable and block final approval.

## Generate and Review

1. Use `inputs/` with **CPERS / 1Q26**. For the original quarter, select `fixtures/4Q25/` with **CPERS / 4Q25**. For custom data, select its source folder and enter its client and quarter.
2. Select **Generate Draft**. The review checklist links to source issues, financial checks and charts.
3. Compare chart readings with their source images. A correction needs a reason and creates a new draft. Audit details are available in expandable views.
4. Fix source blockers and regenerate. Review warnings, confirm charts, enter your name and approve. Successful approval downloads the final PDF.

Draft filenames follow `<CLIENT>_PMR_<QUARTER>_DRAFT.pdf`; approved filenames omit `_DRAFT`. Approval is tied to the draft, source and implementation hashes. Changed files require a new review.

The supplied 1Q26 draft **cannot be finalized**: portfolio IRR and multiple are absent, and the allocation history gives a $515M target versus $501,248,068.80 in the flash. Supported sections remain available without inventing the missing figures.

## Engineering and Verification

File discovery uses contents, not filenames. Money uses `Decimal` and rejects fractions of a cent; rates and percentages are finite floats used as supplied. Calculations, rankings and compliance run in code. Models read chart images and write connecting prose using numerical placeholders and cited passages. Code checks the figures and citations; a second model pass checks the prose. Human review remains required.

Temperature 0, an OpenAI seed and a content-hash cache reduce variation; they do not guarantee identical fresh model responses. The saved identical-PDF result used two fresh output folders with the same cached responses and **zero new API calls**. Financial results and structured selections are checked separately from prose wording.

On `round2-clean`, a fresh macOS/Python 3.12 install passed **246 tests** and **58/58 original-quarter financial checks**. Two separate no-key processes also matched. After setup, run:

```powershell
.\.launcher-venv\Scripts\python.exe -m pytest -q
.\.launcher-venv\Scripts\python.exe scripts/verify_repeatability.py --client CPERS --quarter 4Q25 --inputs fixtures/4Q25
.\.launcher-venv\Scripts\python.exe scripts/rehearse_unseen.py
```

On macOS/Linux, use `.launcher-venv/bin/python`. These commands disable paid model calls. To test an isolated install, first run `scripts/package_submission.py`, then `scripts/verify_clean_install.py` with Python 3.12.

The [verification record](submission/verification.json) names the branch and scope for each result. The submitted `round2-v2-final` passed [Windows and macOS CI](https://github.com/abdullahw1/vectera-pmr-agent/actions/runs/37577623114). The later input-delivery branch passed on macOS, but Windows failed one new test because path separators differed; this branch fixes that comparison. A Windows 11 interactive demo is separate from CI and has not been verified.

## Submission History

Evaluated v1 is frozen at [`v1-submission`](https://github.com/abdullahw1/vectera-pmr-agent/tree/v1-submission). It found the moved total row by label, then stopped on its blank IRR at `ReturnsMultiples(Agg)/V28`, before model calls. Fund-level blanks were tolerated but aggregate blanks were not: an inconsistent missing-value policy, not a hardcoded-cell failure. Both original runs are recorded in [v1-execution.json](submission/v1-execution.json).

The first v2 repair (`23cdf82`) changed two production files and added six tests. Later v2 work added related validation, contextual source checks (including Tidewater's termination) and review controls. Counts from the first repair do not describe the final branch. The previously submitted `round2-v2-final` branch and v1 tag are unchanged; this `round2-clean` branch fixes the delivery/test layout, not the reporting logic. The emailed rerun note is supplied separately.

```text
pmr/          reporting pipeline and browser UI
inputs/       received 1Q26 source package
fixtures/     original 4Q25 regression sources
tests/        regression, messy-input and approval tests
scripts/      launcher, packaging and verification
submission/   1Q26 draft, v1 result and verification/audit records
SPEC.md       assignment requirements
```

New runs go in ignored `output/`. `submission/audit.zip` contains the saved draft's manifest, evidence, review queue and historical verification records. Old run paths inside those records are retained as originally recorded, not instructions to follow. Earlier snapshots remain in Git history rather than duplicate folders.
