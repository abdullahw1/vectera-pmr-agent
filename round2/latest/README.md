# Latest Optional V2 Delivery

Branch: **`round2-v2-final`**. Evaluated v1 remains frozen at **`v1-submission`**. No original input files were edited, and main and the earlier v2 branch remain unchanged.

## Submission Files

- [One-page investigation note](../Abdullah_Waheed_CPERS_1Q26_Rerun_Note.pdf): the unchanged v1 failure, related reader policies, source findings and current corrections.
- [Unchanged v1 failure](../v1/failure.json): no PDF was produced by v1.
- [Latest 1Q26 draft](CPERS_PMR_1Q26_DRAFT.pdf): generated from this delivery's code, with the complete [original flash exhibit](flash-exhibit.zip) provided separately.
- [Review queue](review.md), [financial verification](verification.json), [claim manifest](manifest.json), [evidence ledger](evidence.json), [semantic manifest](semantic_manifest.json), and [run diagnostics](diagnostics.json).
- [Full test log](full-tests.log) and [test execution record](full-tests.json).
- [Output checks](output-checks.json): 13 portrait pages, eight core tables and all 889 raw source PDF cells retained in the audit.
- [Current cached repeatability](cached-repeatability.json) and [original-quarter regression](4Q25-regression.json).

## Changes After the Initial V2

The initial fix allowed missing aggregate IRR and multiple values to reach a truthful, blocked draft instead of stopping generation. Additional work covers malformed numbers, incomplete holdings and cash data, missing or ambiguous schema information, damaged supporting files, and cleanup of stale artifacts after a failed rerun. Essential unreadable inputs still stop generation; missing data is never replaced with an invented number. See [the error-handling inventory](../../PREVIEW_ERROR_HANDLING.md).

The workspace now opens the PDF first, with paging and zoom, a compact review checklist, side-by-side chart review and plain-language source issues. Evidence, grouped warnings, model usage and audit records remain available behind expandable controls and drawers. Release checks have not been weakened. See [interface details](../../PREVIEW_UI.md).

## Observed Results

The current code passed **229 tests** on macOS/Python 3.12 with model API access disabled for the test suite. Earlier desktop/mobile interface checks were supplemented by a current desktop check of the 13-page draft and grouped source-context warnings. JavaScript syntax checks passed for both browser pages.

Two fresh output/cache folders seeded with the same 23 saved model responses produced identical financial results, claims and PDF bytes. Each made **zero new API calls** and produced **13 portrait pages**, passing **62 of 63 financial checks**. This checks cached repeatability, not independent live-model wording. The current no-key 4Q25 regression passed **58 of 58** financial checks. The packaged draft and full test record were checked against this delivery's production-code hashes.

The appendix follows the original 3Q25 sample's eight core tables. Composition has five columns; quarterly returns omit mostly blank annual columns; annual net returns show the required 1-/3-/5-year horizons. US/Ex-US classifications move to a source-linked geographic footnote, and duplicate client total rows are removed only when their financial cells match the Vectera total. Cash amounts include separators. The complete flash is supplied in flash-exhibit.zip and retained as appendix.pdf in runtime audit bundles. All original source cells, including omitted detail, remain registered in the evidence ledger. This keeps the flash exhibit available under SPEC 1.11 rather than reducing the report to the newer reference's single schedule without supporting exhibits.

Tidewater's dissolution and the difference between its notice and supplied flash return are explicit. Northgate/Ridgeline contributions are described. Silverline's individual LTV is a warning, not a sleeve-compliance failure. Ten historical target/NAV revisions are linked to both sources; chart labels dating through 4Q25 flag lagged market evidence. These findings appear in the review queue. Financial calculations and approval requirements are unchanged.

The three source blockers remain: missing aggregate IRR, missing aggregate investment multiple, and conflicting allocation targets ($515M in history versus $501,248,068.80 in the flash). No charts were falsely confirmed and no human approval or final PDF is included. The PDF stays DRAFT.

Earlier independent live-model repeatability and original v1/v2 comparison records remain in the [historical delivery guide](../README.md). No new independent live-model repeatability or Windows execution is claimed. Whether the revised history was intentional, why the deck repeats older observations, and the cross-package Cornerstone funded-balance difference need clarification from the source owner, not a guessed correction.

## Run It

Use Python 3.12. Follow the [root README](../../README.md) for API key setup and `start.cmd` on Windows or `python3.12 scripts/launch.py` on macOS/Linux. OpenAI is preferred and takes priority when both keys are set. Select the received 1Q26 package's `inputs` folder, enter **CPERS / 1Q26**, and select **Generate Draft**.

The complete received input package, API keys, model cache and local approval records are not republished. The flash PDF alone is reproduced as a supplementary exhibit. Records retain original run paths and identify the hosts actually tested.
