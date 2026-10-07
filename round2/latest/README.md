# Latest Optional V2 Delivery

Branch: **`round2-v2-final`**. Evaluated v1 remains frozen at **`v1-submission`**. No original input files were edited, and main and the earlier v2 branch remain unchanged.

## Submission Files

- [One-page investigation note](../Abdullah_Waheed_CPERS_1Q26_Rerun_Note.pdf): the unchanged v1 failure, source issues and initial focused repair.
- [Unchanged v1 failure](../v1/failure.json): no PDF was produced by v1.
- [Latest 1Q26 draft](CPERS_PMR_1Q26_DRAFT.pdf): generated from this delivery's production code through the local workspace.
- [Review queue](review.md), [financial verification](verification.json), [claim manifest](manifest.json), [evidence ledger](evidence.json), [semantic manifest](semantic_manifest.json), and [run diagnostics](diagnostics.json).
- [Full test log](full-tests.log) and [test execution record](full-tests.json).
- [Appendix cleanup checks](appendix-checks.json): all 414 distinct entity/metric/value facts retained, with three redundant tables removed.

## Changes After the Initial V2

The initial fix allowed missing aggregate IRR and multiple values to reach a truthful, blocked draft instead of stopping generation. Additional work covers malformed numbers, incomplete holdings and cash data, missing or ambiguous schema information, damaged supporting files, and cleanup of stale artifacts after a failed rerun. Essential unreadable inputs still stop generation; missing data is never replaced with an invented number. See [the error-handling inventory](../../PREVIEW_ERROR_HANDLING.md).

The workspace now opens the PDF first, with paging and zoom, a compact review checklist, side-by-side chart review and plain-language source issues. Evidence, grouped warnings, model usage and audit records remain available behind expandable controls and drawers. Release checks have not been weakened. See [interface details](../../PREVIEW_UI.md).

## Observed Results

The current code passed **223 tests** on macOS/Python 3.12 with model API access disabled for the test suite. Desktop and mobile browser checks of the review interface were performed separately before the appendix-only cleanup. JavaScript syntax checks passed for both browser pages.

The fresh CPERS / 1Q26 workspace run originally produced 15 portrait pages and made 23 OpenAI requests. The latest appendix cleanup reused all 23 saved responses, made **zero new API calls**, and produced **14 portrait pages**, still passing **62 of 63 financial checks**. All non-appendix data and the first ten pages are unchanged. Before packaging, the draft's implementation hashes and the test record's source hashes were checked against this delivery's code.

The empty since-inception table and the duplicate 3-/5-year table are omitted. When an IRR/multiple table contains only market values, those values move into the quarterly returns table instead. Unique reported figures, including real zeros, remain visible and source-linked. A short note explains omitted sections. The original 4Q25 exhibits are unchanged.

The three source blockers remain: missing aggregate IRR, missing aggregate investment multiple, and conflicting allocation targets ($515M in history versus $501,248,068.80 in the flash). No charts were falsely confirmed and no human approval or final PDF is included. The PDF stays DRAFT.

This latest run is a single live generation, not a new two-run repeatability experiment. Earlier repeatability and 4Q25 comparison records remain in the [historical delivery guide](../README.md). Historical allocation revisions and Tidewater's omitted termination commentary remain disclosed limitations. Windows execution is not claimed.

## Run It

Use Python 3.12. Follow the [root README](../../README.md) for API key setup and `start.cmd` on Windows or `python3.12 scripts/launch.py` on macOS/Linux. OpenAI is preferred and takes priority when both keys are set. Select the received 1Q26 package's `inputs` folder, enter **CPERS / 1Q26**, and select **Generate Draft**.

The received 1Q26 input package, API keys, model cache and local approval records are not republished in this delivery. The records retain original run paths and identify the hosts actually tested.
