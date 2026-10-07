# CPERS 1Q26 Results

The evaluated submission is frozen at **`v1-submission`** (`618b990`). This branch, **`round2-v2-final`**, contains v2. The rerun note is attached separately to the submission email.

## Current delivery

| File | Purpose |
| --- | --- |
| [V1 failure](v1/failure.json) | Unchanged v1 stopped at the blank aggregate IRR; no PDF was produced. |
| [V1 execution record](v1/execution-verification.json) | Original run environment and preservation checks. |
| [V2 draft PDF](latest/CPERS_PMR_1Q26_DRAFT.pdf) | Current 13-page report, not approved for release. |
| [Review issues](latest/review.md) | Missing figures, conflicting sources and review warnings. |
| [Financial checks](latest/verification.json) | 62/63 checks passed; allocation target mismatch remains. |
| [Source manifest](latest/manifest.json) / [evidence](latest/evidence.json) | Figures and claims linked to source cells, pages and passages. |
| [Full test result](latest/full-tests.json) / [log](latest/full-tests.log) | 229 tests passed on macOS/Python 3.12. |
| [4Q25 regression](latest/4Q25-regression.json) | 58/58 original-quarter checks passed. |
| [Cached repeatability](latest/cached-repeatability.json) | Two fresh runs with the same cached responses produced identical PDFs, with no new API calls. |
| [Output checks](latest/output-checks.json) | Page layout, eight core appendix tables and source-cell coverage. |
| [Complete flash exhibit](latest/flash-exhibit.zip) | Original flash PDF supplied alongside the compact appendix. |

V2 treats missing aggregate IRR and multiple as unavailable instead of aborting the whole report. Both still block approval, as does the allocation target conflict ($515M in history versus $501,248,068.80 in the flash). No input values were changed to make the report pass.

The review queue also records Tidewater's termination, individual fund LTV, historical allocation revisions and lagged market data. Chart readings and commentary still require human review. Separate live model calls may differ in wording. No Windows run or approved final PDF is claimed.

## Reproduce

Follow the [root setup guide](../README.md). Select the received package's `inputs` folder and run **CPERS / 1Q26**. For unchanged v1, use a separate checkout of `v1-submission` with the same input package and a fresh output folder.

`archive/` retains historical results from the initial focused repair; `latest/` is the current delivery. Original 4Q25 artifacts are in `../output/`. These older records are retained for comparison, not presented as runs of the current code.
