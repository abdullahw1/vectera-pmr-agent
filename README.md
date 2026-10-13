# Vectera PMR Agent

Generates a quarterly Performance Measurement Report from source documents. Select a client and quarter; the agent finds the relevant files, calculates figures in code, and uses a model for chart reading and source-backed commentary. Reports remain drafts until reviewed and approved.

## Round-two submission

This branch is **`round2-1q26-inputs`**: the submitted v2 code with the received **1Q26 source package included in `inputs/`**. The original 4Q25 package is preserved in `fixtures/4Q25/` for regression tests. The evaluated v1 is preserved at [tag `v1-submission`](https://github.com/abdullahw1/vectera-pmr-agent/tree/v1-submission); main and the previously submitted `round2-v2-final` branch are unchanged.

- [V1 result](round2/v1/failure.json): both unchanged CPERS / 1Q26 runs stopped at the missing aggregate IRR in `ReturnsMultiples(Agg)/V28`, before model calls or a PDF.
- [V2 1Q26 draft](round2/latest/CPERS_PMR_1Q26_DRAFT.pdf): 13 portrait pages, with missing figures shown as unavailable and final approval blocked.
- [Results and audit files](round2/README.md): tests, repeatability, review issues and source locations. The one-page rerun note is supplied separately by email.

## Start the app

Use **Python 3.12**. First-time setup needs internet access. No Docker or database is required.

**Windows 11:** download this branch using **Code > Download ZIP**, extract it, and open PowerShell in the folder containing `start.cmd`. Check Python, then launch:

```powershell
py -3.12 --version
.\start.cmd --client CPERS --quarter 1Q26 --output output/rerun-1Q26
```

**macOS / Linux:**

```bash
python3.12 scripts/launch.py --client CPERS --quarter 1Q26 --output output/rerun-1Q26
```

The launcher creates a local environment, installs pinned dependencies and opens the browser. Keep the terminal open; Ctrl+C stops the app. The terminal prints the localhost URL.

## Add an API key

**OpenAI is preferred; only one provider key is needed.** Existing environment variables take priority, so evaluator-provided keys need no file changes. Otherwise, copy `.env.example` to `.env` and add your key. On Windows:

```powershell
Copy-Item .env.example .env
notepad .env
```

```dotenv
OPENAI_API_KEY="your-key-here"
```

Edit rather than overwrite an existing `.env`. It is ignored by Git. Restart the app after changing keys. Source passages and chart images are sent to the selected provider's API.

OpenAI takes priority if both keys are set. Defaults are `gpt-4.1-2025-04-14` for prose and `gpt-4.1-mini-2025-04-14` for charts; `PMR_MODEL` and `PMR_VISION_MODEL` can override them. Anthropic is supported through `ANTHROPIC_API_KEY` with default `claude-sonnet-4-6`; unset `OPENAI_API_KEY` to select it. Cross-workspace Anthropic keys requiring a workspace-ID header are not supported.

Without a key, financial calculations and report generation still run. Commentary uses attributed source excerpts; image-only chart readings remain unavailable and block approval.

## Generate and review

1. The default `inputs/` folder now contains the complete **CPERS / 1Q26** rerun package (15 source files, including nine manager reports). Enter **CPERS / 1Q26**, or use the launch command above to prefill them. To reproduce the original quarter, choose `fixtures/4Q25/` and enter **CPERS / 4Q25**. For another package, choose its folder and enter its client and quarter.
2. Select **Generate Draft**. The report opens with a checklist linking to charts, source issues and financial checks.
3. Review chart values beside their source images. Corrections require a reason and create a new draft to review. Technical details and audit records are available in expandable views.
4. Resolve blockers by correcting source data and generating a new draft. Inspect warnings, confirm charts and complete **Final approval**. Successful approval downloads the final PDF; a download link remains available.

Drafts are named `<CLIENT>_PMR_<QUARTER>_DRAFT.pdf`; approved reports omit `_DRAFT`. Approval is tied to hashes of the draft, inputs and implementation. Changed files require a new review.

The 1Q26 example cannot be finalized: aggregate IRR and multiple are missing, and allocation history gives a $515M target versus $501,248,068.80 in the flash. V2 retains supported sections without inventing the missing values.

## Command line and tests

After the launcher has installed dependencies, use its environment:

```powershell
.\.launcher-venv\Scripts\python.exe -m pmr generate --client CPERS --quarter 1Q26 --output "output\rerun-1Q26"
.\.launcher-venv\Scripts\python.exe -m pytest -q
.\.launcher-venv\Scripts\python.exe scripts/verify_repeatability.py --client CPERS --quarter 4Q25 --inputs fixtures/4Q25
.\.launcher-venv\Scripts\python.exe scripts/rehearse_unseen.py
```

On macOS/Linux, substitute `.launcher-venv/bin/python`. Tests and the default repeatability/rehearsal commands do not require paid model calls.

Submitted v2 results: **229 tests passed**, **58/58 original-quarter financial checks**, and two fresh 1Q26 runs with the same cached responses produced identical PDFs. This input-delivery branch passed **231 tests**, including two new delivery tests, plus a fresh no-key 1Q26 run and original-quarter repeatability. See [the input-delivery verification](round2/input-package-verification.json). Cached repeatability is not a guarantee of identical wording from separate live calls. Runs were verified on macOS/Python 3.12; Windows execution was not personally observed. CI is configured for Windows and macOS.

The included 1Q26 files are byte-identical to the received package, excluding Finder metadata only. New delivery tests compare their hashes against the original v1 execution record and exercise a no-key 1Q26 draft. The reporting code under `pmr/` is unchanged; test paths, verification commands and packaging were updated for the new folder layout. Existing artifacts under `output/` are historical 4Q25 results, so the launch command uses a separate 1Q26 output folder.

## How it works

File selection uses document contents, not filenames. Financial calculations, rankings and compliance stay in code. The model writes with numerical placeholders and cited passages; code restores source figures, and a second model pass checks the prose. Missing evidence is flagged rather than invented. Essential unreadable inputs stop generation; other missing figures can remain unavailable in a blocked draft.

Every reported figure and claim has source locations in the audit records. The appendix uses eight core sample-style tables; the complete flash exhibit and omitted source cells remain available separately.

```text
pmr/       pipeline and browser interface
tests/     regression and guardrail tests
scripts/   launcher and verification utilities
inputs/    received 1Q26 source package, unchanged
fixtures/  original 4Q25 package for regression tests
round2/    v1 result and current v2 report/verification
output/    original 4Q25 artifacts; default folder for new runs
SPEC.md    assignment requirements
```
