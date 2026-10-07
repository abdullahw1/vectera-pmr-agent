# CPERS 1Q26 Rerun Note

Abdullah Waheed

## What happened in v1

I froze the evaluated code at 618b990, tagged v1-submission, and ran it twice unchanged on CPERS / 1Q26. Discovery worked. Both runs stopped at ReturnsMultiples(Agg)/V28 before any model calls, so neither produced a PDF. The Vectera total's IRR and multiple are blank at V28/W28. The CPERS total and flash PDF have the same gaps. I allowed missing fund returns but assumed these totals existed. The renderer formatted them directly as numbers. My tests missed that boundary.

## The fix and the same pattern elsewhere

V2 records missing totals with their source cells, prints "not available", and blocks approval. It never substitutes zero, last quarter's value or a manager's lifetime return. I extended that review to other readers rather than stopping at the first failing cell.

| Input | Policy and test coverage |
| --- | --- |
| Missing fund or total returns | Keep the source cell and show unavailable. Tests cover either total, both, and real zero. |
| Incomplete cash or holding NAV | Keep the holding; withhold incomplete rankings and totals. Tests cover missing rows and values. |
| Malformed numbers or essential schema | Stop with a source-specific error. Tests cover text, non-finite numbers, missing sheets and ambiguous columns. |
| Missing manager evidence | Continue with a warning, without invented drivers. Source-matching and narrative tests cover this. |

The latest draft reports $539.8M committed or approved and 17 flash-carried/open positions. It passes 62 of 63 financial checks. Three blockers remain: missing IRR, missing multiple, and the target conflict. Full test results are linked with the code. Two fresh output folders using the same saved model responses produced identical figures, claims and PDF bytes. Earlier independent live-model runs matched financial results but differed in wording. Local runs used macOS/Python 3.12, not Windows.

## Source issues I found

The history target is $515M for 1Q26; the flash says $501.25M. All eight overlapping target points were revised, including 4Q25 from $496M to $512M. Two historical NAV points changed. V2 now compares the history with the prior report's table and flags revisions without replacing either source.

The seven market-chart images are unchanged from the original package. Their latest labelled observations are 4Q25. V2 flags the lag and labels the discussion accordingly. Tidewater's notice confirms dissolution and presents no quarterly percentages, while the flash supplies 5.25%. The report explains both and requests review. Silverline's 50.8% individual LTV is flagged separately; SPEC's sleeve-level compliance test still passes. Northgate and Ridgeline's $12M and $7.5M funding is explicit.

## Judgment calls and limits

I keep zero-NAV Tidewater in the flash-carried count. Beacon Hill's PM approval passes SPEC's four filters; the prior report also includes a PM-approved commitment. Kestrel has no manager report, so I add no drivers. Cornerstone's funded balance increased by $560,000 versus the original package despite no recorded contribution; that equals its distribution. I disclose it as unexplained, not a proven error. The appendix keeps the original sample's core tables, with the complete flash and detailed facts in the audit package. Charts, source conflicts and prose still need human review. I used AI coding assistants during implementation and review. V1 and the supplied inputs remain unchanged.
