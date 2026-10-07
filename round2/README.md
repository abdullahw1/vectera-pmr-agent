# CPERS 1Q26 Rerun Submission

The evaluated v1 is frozen at tag **`v1-submission`**, commit `618b990a66a2940fac7f7d65fa6f7768c9d89652`.
This branch, **`round2-v2-final`**, contains the latest optional v2. Main and the frozen tag are unchanged.
The earlier focused v2 remains available on `codex/round2-v2`.

## Read First

- [One-page note](Abdullah_Waheed_CPERS_1Q26_Rerun_Note.pdf), also available as [editable text](RERUN_NOTE.md).
- [Original unchanged v1 result](v1/failure.json): both runs stopped at `ReturnsMultiples(Agg)/V28`; no PDF was produced.
- [Latest V2 1Q26 draft](latest/CPERS_PMR_1Q26_DRAFT.pdf): 13 portrait pages, not approved for release.
- [Latest delivery and verification](latest/README.md): current code, tests and run results.
- [Latest review queue](latest/review.md): blockers, warnings, and items requiring review.
- [Latest audit manifest](latest/manifest.json): report claims and figures linked to their source locations.

## What Changed

The initial focused fix changed only `pmr/finance.py` and `pmr/report.py` in production code. Aggregate IRR and net multiple now use the existing missing-value path. Blank figures retain their source cells, display as `not available`, and block final approval. Real zero remains zero. Present figures keep the original wording.

The latest delivery adds targeted input validation, safer failed-run handling, source-context warnings and a report-first review interface. It passed 229 tests. The appendix now uses the original sample's core tables, with the complete flash supplied separately and all source cells retained in the audit. The same three source blockers remain. Start with [the current delivery guide](latest/README.md).

## Earlier Focused V2 Results

The results in this section and `v2/` describe the earlier focused v2, not a new execution of the latest code. The one-page note and latest-delivery guide describe the current corrections as well as the original failure.

Six tests were added in `tests/test_missing_portfolio_returns.py`. The initial isolated v2 copy passed all 167 tests. Its initial two-file repair is preserved in the earlier v2 branch; the current branch includes subsequent changes. That initial no-key 4Q25 comparison produced byte-identical v1/v2 PDFs and the same 58 checks. The latest PDF layout and prose are intentionally different.

Two independent live OpenAI 1Q26 runs matched financial figures, roles, approvals, compliance, chart observations, missing-value states, and report structure. Prose differed, so PDF bytes did not match. Two independent no-key drafts were byte-identical. These are observed results, not guarantees for future model responses.

## Why the Draft Is Blocked

The source does not report aggregate IRR or net multiple. Allocation history also shows a $515M target for 1Q26 while the flash reports $501,248,068.80. The overview follows the flash and the history chart retains the conflicting source series. The draft passes 62 of 63 checks; the failed check concerns that target mismatch, and the two missing figures are separate release blockers.

Earlier allocation-history points were revised too. Current code compares them with the prior report's table and surfaces warnings. Tidewater's termination is included, with the flash return distinguished from the manager notice. The note explains the flash-carried position count, Beacon Hill's PM approval and unresolved source questions. No input values were changed to force a clean report.

## Reproduce on the Supplied Inputs

The received 1Q26 input package is intentionally not republished here. Extract your copy and select its `inputs` folder. API keys still come from the environment or a local ignored `.env`; OpenAI takes priority when both provider keys exist. See the [main README](../README.md#add-an-api-key) for key setup.

On Windows 11 with Python 3.12, run `start.cmd` from the repository root. In the browser, choose the received inputs folder, enter `CPERS` and `1Q26`, and generate a report. The saved artifacts here are evidence from earlier runs, not a preapproved review session.

For the CLI, after installing `requirements.txt` into a Python 3.12 environment:

```powershell
python -m pmr generate --client CPERS --quarter 1Q26 --inputs "C:\path\to\received\inputs" --output "output\rerun-1Q26"
```

For unchanged v1, use a separate checkout of `v1-submission` and run the same command with a fresh output folder. Do not edit its code or the input documents.

## Verification Records

For the current branch, use [the latest test log](latest/full-tests.log), [test record](latest/full-tests.json), and [fresh-run verification](latest/verification.json). The following links preserve the earlier focused v2 evidence.

- [Test results](verification/test-results.json).
- [Six tests rerun in this delivery checkout](verification/delivery-test-results.json).
- [Original-quarter v1/v2 regression](verification/4Q25-regression.json).
- [No-key repeatability](verification/no-key-repeatability.json).
- [Live-model repeatability](verification/live-repeatability.json).
- [Unavailable values and rejected approval checks](verification/output-checks.json).
- [V1 preservation verification](verification/v1-preservation.json).
- [V2 run diagnostics](v2/diagnostics.json), [financial verification](v2/verification.json), [semantic manifest](v2/semantic_manifest.json), and [evidence ledger](v2/evidence.json).

Records preserve the original local paths and run times. They describe existing macOS/Python 3.12 runs, not Windows or fresh-install verification. The full suite result comes from the tested isolated v2 copy; the code is unchanged in this delivery checkout. Chart values and prose still need genuine human review. No human approval or final PDF is included.
