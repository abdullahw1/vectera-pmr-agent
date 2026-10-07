# Review Interface Preview

These changes belong to `codex/round2-preview`, not the evaluated v1 or the published round-two submission. Financial calculations, source-selection rules and release requirements are unchanged by this interface work.

## What changed

- One workflow: Documents, Generate, Review, Finalize. The selected document package and configured API provider are visible before generation; credentials are never sent to the browser.
- The report opens first. Page navigation and zoom use images rendered directly from the hash-checked PDF rather than relying on browser PDF plugins. The original PDF remains downloadable.
- A compact checklist links to source blockers, chart confirmations and warnings. Blockers are shown first; repeated warnings are grouped and expandable.
- Charts display the source image beside the extracted values. Corrections require a reason. Advanced JSON editing remains available behind a disclosure.
- Source evidence opens in a drawer. Missing values say "Not reported in the source" and retain their file, sheet and cell references.
- Model usage, processing stages, financial checks and machine-readable audit records live under Run details & audit. Existing upload, run-history, audit-bundle and approval features remain available.
- Final approval is expandable. Successful approval initiates the final PDF download and retains a download link. Corrected charts still create a new draft for review instead of silently approving it.
- Older drafts can be inspected with the current interface without modifying their saved records. A changed implementation still requires a fresh draft before approval.

## Verification

The full suite passed: **220 tests**, on macOS with Python 3.12, with API keys disabled for the tests. New tests cover draft and final preview hashes, tampered PDFs and payloads, outdated implementation detection, safe runtime encoding, and provider metadata that excludes credentials. Both browser scripts passed JavaScript syntax checks.

Live browser checks covered desktop and a 390-by-844 mobile viewport: report paging and zoom, issue details, source drawers, grouped warnings, chart readings, and readable run diagnostics. No browser errors were recorded during these checks.

A fresh CPERS / 1Q26 generation was also started from the workspace. It produced a 15-page draft with 62 of 63 financial checks passing and the existing three source blockers. It used 23 OpenAI requests, with no failed requests. Approval remained disabled; no genuine chart confirmations or human approval were fabricated. Automated final-report tests use disposable test outputs, not submission artifacts.

Local verification logs are stored outside the repository in `Vectera_Round2/ui-presentation-verification`; the fresh browser run is `33839e3fdde1` under `Vectera_Round2/ui-preview/runs`. This was not a Windows browser verification.
