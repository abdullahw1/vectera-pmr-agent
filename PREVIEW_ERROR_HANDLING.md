# Supplementary Preview Error Handling

This work is on `codex/round2-preview`, separate from the published round-two submission on `codex/round2-v2`. The earlier note and run evidence under `round2/` describe that published v2, not these additional changes. Frozen v1 and the official input package are unchanged.

## Behavior

| Case | Result |
| --- | --- |
| Missing fund income, fees, appreciation, beginning/ending value, or LTV | A source-linked partial draft with blockers; dependent calculations remain unavailable. Contributor/detractor ranks are withheld when their required inputs are incomplete. |
| Missing fund return | A recorded unavailable fact, including the source cell when the row exists. No zero is invented. |
| Blank contribution/distribution/withdrawal | Still zero under the existing explicit capital-flow rule. |
| Missing required sheet, column, label, benchmark, or core aggregate figure | Clear failure describing the missing structure or source location. No guessing or partial sum presented as a complete total. |
| Duplicate headers or ambiguous matching columns/rows | Generation stops instead of choosing one silently. |
| Boolean, non-finite, text, excessive-precision, or fractional-cent money | Rejected, with file/sheet/cell context. |
| Damaged workbook | Structured failure identifying unreadable workbooks when the requested flash cannot be found. |
| Damaged supporting deck | A blocked financial draft may still be produced; the deck is flagged as unreadable. |
| Zero or unavailable allocation denominator | Clear validation failure rather than division by zero. |
| Filesystem failure or unexpected generation exception | Structured failure classification and an actionable message; unexpected failures retain frame locations without raw exception values. Configured API keys are redacted. |
| Failed rerun or failure after rendering | Previously generated report/review/approval artifacts are removed when writable; diagnostic progress is retained. |
| Output inside the source folder | Rejected before modifying source documents. Failure records are not written into the input folder. |

Safe partial drafts are different from incomplete core data. The latter can still stop PDF generation. A clear refusal is better than a report based on guessed values. These changes do not fill missing IRR/multiple values or resolve conflicting allocation history.

## Verification

The full suite passed **208 tests**, including **41 additional failure-handling tests**. An initial full run caught a validation check placed too early in financial parsing. It was moved to report generation, and the existing different-client test now passes without weakening it.

The final preview generated CPERS 1Q26 with unchanged golden figures and the existing three release blockers. The last integration run reused 23 saved model responses and made no new API calls. The original no-key 4Q25 PDF remained byte-identical to v1 and passed its 58 checks. Live UI smoke checks returned HTTP 400 with readable messages for an invalid quarter, missing folder, and malformed request.

Local logs and verification records are stored outside the repository at `/Users/abdullahwaheed/Downloads/Vectera_Round2/error-handling-preview`. These were macOS/Python 3.12 checks, not Windows verification. No claim is made that every possible failure is covered.

## Try the UI

The local preview runs at `http://127.0.0.1:8768/`. Start a new report after a code change; older drafts cannot be approved against a different implementation hash. Do not alter the official inputs to manufacture a clean report. For messy-input testing, use disposable copies, as the automated tests do.
