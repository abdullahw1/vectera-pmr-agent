# Vectera PMR Agent

Generates a quarterly Performance Measurement Report from source documents. Select a client and quarter; the agent finds the relevant files, calculates figures in code, and uses a model for chart reading and source-backed commentary. Reports remain drafts until reviewed and approved.

## Round-two submission

This branch is **`round2-v2-final`**. The evaluated v1 is preserved at [tag `v1-submission`](https://github.com/abdullahw1/vectera-pmr-agent/tree/v1-submission); main is unchanged.

- [V1 result](round2/v1/failure.json): both unchanged CPERS / 1Q26 runs stopped at the missing aggregate IRR in `ReturnsMultiples(Agg)/V28`, before model calls or a PDF.
- [V2 1Q26 draft](round2/latest/CPERS_PMR_1Q26_DRAFT.pdf): 13 portrait pages, with missing figures shown as unavailable and final approval blocked.
- [Results and audit files](round2/README.md): tests, repeatability, review issues and source locations. The one-page rerun note is supplied separately by email.

## Start the app

Use **Python 3.12**. First-time setup needs internet access. No Docker or database is required.

**Windows 11:** download this branch using **Code > Download ZIP**, extract it, and open PowerShell in the folder containing `start.cmd`. Check Python, then launch:

```powershell
py -3.12 --version
.\start.cmd
```

**macOS / Linux:**

```bash
python3.12 scripts/launch.py
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

1. Choose the document folder and enter the client and quarter. The included `inputs/` package is **CPERS / 4Q25**. For the rerun, select the received **1Q26 package's `inputs` folder** and enter **CPERS / 1Q26**. That full package is not republished here.
2. Select **Generate Draft**. The report opens with a checklist linking to charts, source issues and financial checks.
3. Review chart values beside their source images. Corrections require a reason and create a new draft to review. Technical details and audit records are available in expandable views.
4. Resolve blockers by correcting source data and generating a new draft. Inspect warnings, confirm charts and complete **Final approval**. Successful approval downloads the final PDF; a download link remains available.

Drafts are named `<CLIENT>_PMR_<QUARTER>_DRAFT.pdf`; approved reports omit `_DRAFT`. Approval is tied to hashes of the draft, inputs and implementation. Changed files require a new review.

The 1Q26 example cannot be finalized: aggregate IRR and multiple are missing, and allocation history gives a $515M target versus $501,248,068.80 in the flash. V2 retains supported sections without inventing the missing values.

## Command line and tests

After the launcher has installed dependencies, use its environment:

```powershell
.\.launcher-venv\Scripts\python.exe -m pmr generate --client CPERS --quarter 1Q26 --inputs "C:\path\to\received\inputs" --output "output\rerun-1Q26"
.\.launcher-venv\Scripts\python.exe -m pytest -q
.\.launcher-venv\Scripts\python.exe scripts/verify_repeatability.py --client CPERS --quarter 4Q25
.\.launcher-venv\Scripts\python.exe scripts/rehearse_unseen.py
```

On macOS/Linux, substitute `.launcher-venv/bin/python`. Tests and the default repeatability/rehearsal commands do not require paid model calls.

Recorded results: **229 tests passed**, **58/58 original-quarter financial checks**, and two fresh 1Q26 runs with the same cached responses produced identical PDFs. Cached repeatability is not a guarantee of identical wording from separate live calls. Runs were verified on macOS/Python 3.12; Windows execution was not personally observed. CI is configured for Windows and macOS.

## How it works

File selection uses document contents, not filenames. Financial calculations, rankings and compliance stay in code. The model writes with numerical placeholders and cited passages; code restores source figures, and a second model pass checks the prose. Missing evidence is flagged rather than invented. Essential unreadable inputs stop generation; other missing figures can remain unavailable in a blocked draft.

Every reported figure and claim has source locations in the audit records. The appendix uses eight core sample-style tables; the complete flash exhibit and omitted source cells remain available separately.

```text
pmr/       pipeline and browser interface
tests/     regression and guardrail tests
scripts/   launcher and verification utilities
inputs/    original 4Q25 source package
round2/    v1 result and current v2 report/verification
output/    original 4Q25 artifacts; default folder for new runs
SPEC.md    assignment requirements
```
