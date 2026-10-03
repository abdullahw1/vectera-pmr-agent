# Applicant Review and Release

This checklist is not an approval. Automated extraction and assistant inspection do not replace the actual reviewer's judgment.

## Inspect the draft

Start `python -m pmr review`, then open its printed local URL. On Windows, use `start.cmd` after the separate Windows smoke test. Click a paragraph/table to trace its inputs. Use Inspect Chart for each market-image review item. Compare every category/legend pair, not just the latest value printed in the condensed report.

| Slide | Important checks |
|---|---|
| 4 | Latest quarter 1.0%, one-year 3.3%, three-year -2.4%, five-year 3.3%. This is not the client benchmark. |
| 5 | Eight periods and two legends; latest cap rate 4.6% and Treasury 4.2%. Points lack value labels: gridline readings, not exact labels. |
| 6 | Twelve unlabeled bars. Residential 2.2/1.4/1.3; Industrial 1.7/1.3/1.8; Office .6/.4/.4; Retail .2/.2/.1. All are approximate % readings. |
| 7 | Industrial one/three/five-year 4.4/1.6/10.2; specialized 5.5/4.0/11.8. Check the legend, which changes the meaning. |
| 8 | Latest own/rent costs $3,400/$2,500 monthly. Compare all five labeled periods. |
| 9 | Latest appraisal/transaction 5.6/7.7%; preceding 5.6/6.3%. Code computes the gap widening from .7 to 2.1 percentage points. Earlier points also require inspection. |
| 10 | Eight cities, two legends; approximate readings. Austin 65/30 and Charlotte 38/17 are the strongest inventory/population differences. |

These are reference readings from the supplied synthetic images, not production constants. A changed input requires a fresh inspection. Correct chart JSON only when the visible image supports the correction, and enter a specific reason. Money corrections belong in the source workbook followed by regeneration.

## Review the warnings

- The realized-only row has a $0.51 roll-forward difference. It is outside the active portfolio; preserve the disclosed warning rather than altering its source.
- Meridian lacks a manager report. Confirm that the report gives flash figures and no invented asset-level causes.
- Allocation history has no client column. The requested-period NAV/target agree with the flash at displayed precision, but ownership remains an assumption.

Read the full PDF, including all appendix panels, and the two-page write-up. Confirm that the limitations describe what was actually observed. Enter your actual reviewer name, acknowledge the review, confirm all seven chart extractions, and approve only when satisfied. No automatic tool should acknowledge on your behalf.

## Package and prepare

After approval, `python scripts/package_submission.py --final` requires the approved report and unchanged inputs. It excludes keys and personal study notes. Keep the draft verification records: they distinguish source accuracy, model repeatability and human approval.

Rehearse the questions in WALKTHROUGH.md. Explain the formulas, which source rows own which statistics, what the model cannot do, how a blocker differs from a warning, and what happens when the input layout falls outside the supported contract. Git publication and sending the submission require your explicit authorization.
