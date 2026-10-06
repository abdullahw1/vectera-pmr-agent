# CPERS 1Q26 Rerun Submission

The evaluated v1 is frozen at tag **`v1-submission`**, commit `618b990a66a2940fac7f7d65fa6f7768c9d89652`.
This branch, **`codex/round2-v2`**, contains the optional focused v2. Main and the frozen tag are unchanged.

## Read First

- [One-page note](Abdullah_Waheed_CPERS_1Q26_Rerun_Note.pdf), also available as [editable text](RERUN_NOTE.md).
- [Original unchanged v1 result](v1/failure.json): both runs stopped at `ReturnsMultiples(Agg)/V28`; no PDF was produced.
- [V2 1Q26 draft](v2/CPERS_PMR_1Q26_DRAFT.pdf): 15 portrait pages, not approved for release.
- [V2 review queue](v2/review.md): blockers, warnings, and items requiring review.
- [Audit manifest](v2/manifest.json): report claims and figures linked to their source locations.

## What Changed

Only `pmr/finance.py` and `pmr/report.py` changed in production code. Aggregate IRR and net multiple now use the existing missing-value path. Blank figures retain their source cells, display as `not available`, and block final approval. Real zero remains zero. Present figures keep the original wording.

Six tests were added in `tests/test_missing_portfolio_returns.py`. The tested v2 copy passed all 167 tests. Its two production files and test file are identical to those on this branch. A fresh no-key 4Q25 comparison produced byte-identical v1/v2 PDFs and the same original 58 checks.

Two independent live OpenAI 1Q26 runs matched financial figures, roles, approvals, compliance, chart observations, missing-value states, and report structure. Prose differed, so PDF bytes did not match. Two independent no-key drafts were byte-identical. These are observed results, not guarantees for future model responses.

## Why the Draft Is Blocked

The source does not report aggregate IRR or net multiple. Allocation history also shows a $515M target for 1Q26 while the flash reports $501,248,068.80. The overview follows the flash and the history chart retains the conflicting source series. The draft passes 62 of 63 checks; the failed check concerns that target mismatch, and the two missing figures are separate release blockers.

Earlier allocation-history points were revised too. Current code checks the requested quarter, not historical revisions. Tidewater's termination is omitted from the report because manager prose is displayed only for ranked funds. The note discloses those limitations, the flash-carried position count, and the Beacon Hill PM-committee interpretation. No input values were changed to force a clean report.

## Reproduce on the Supplied Inputs

The received 1Q26 input package is intentionally not republished here. Extract your copy and select its `inputs` folder. API keys still come from the environment or a local ignored `.env`; OpenAI takes priority when both provider keys exist. See the [main README](../README.md#add-an-api-key) for key setup.

On Windows 11 with Python 3.12, run `start.cmd` from the repository root. In the browser, choose the received inputs folder, enter `CPERS` and `1Q26`, and generate a report. The saved artifacts here are evidence from earlier runs, not a preapproved review session.

For the CLI, after installing `requirements.txt` into a Python 3.12 environment:

```powershell
python -m pmr generate --client CPERS --quarter 1Q26 --inputs "C:\path\to\received\inputs" --output "output\rerun-1Q26"
```

For unchanged v1, use a separate checkout of `v1-submission` and run the same command with a fresh output folder. Do not edit its code or the input documents.

## Verification Records

- [Test results](verification/test-results.json).
- [Six tests rerun in this delivery checkout](verification/delivery-test-results.json).
- [Original-quarter v1/v2 regression](verification/4Q25-regression.json).
- [No-key repeatability](verification/no-key-repeatability.json).
- [Live-model repeatability](verification/live-repeatability.json).
- [Unavailable values and rejected approval checks](verification/output-checks.json).
- [V1 preservation verification](verification/v1-preservation.json).
- [V2 run diagnostics](v2/diagnostics.json), [financial verification](v2/verification.json), [semantic manifest](v2/semantic_manifest.json), and [evidence ledger](v2/evidence.json).

Records preserve the original local paths and run times. They describe existing macOS/Python 3.12 runs, not Windows or fresh-install verification. The full suite result comes from the tested isolated v2 copy; the code is unchanged in this delivery checkout. Chart values and prose still need genuine human review. No human approval or final PDF is included.
