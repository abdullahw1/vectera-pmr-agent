# CPERS 1Q26 Rerun Note

Abdullah Waheed

## What happened with v1

I froze my submitted code as v1 (tag v1-submission, commit 618b990) and ran it twice on CPERS / 1Q26 without changing anything. It found the right files, then stopped before any model calls or PDF generation. Both runs produced the same error.

It failed at V28 in ReturnsMultiples(Agg), where the portfolio's since-inception IRR is blank. The multiple at W28 is blank too. The other portfolio-total row and flash PDF have the same gaps. My code handled missing fund returns but assumed portfolio totals would always exist. My tests missed it. The real mistake was applying two missing-value policies to the same kind of data.

## What I changed in v2

V2 shows the missing figures as "not available", records their exact source cells, and blocks final approval. It never substitutes zero or borrows another source's number. I checked other flash readers for the same pattern: missing cash or NAV keeps the holding but prevents incomplete rankings; malformed numbers and missing essential sheets stop with a clear error; missing manager commentary remains a warning. I added tests for these cases, including a real zero versus a blank.

V2 produces a 13-page draft. The rankings and three open approvals check out: $83M approved, giving $539.8M committed or approved overall. The original 4Q25 run still passes all 58 financial checks. The full suite passes 229 tests. Two fresh runs using the same saved model responses produced identical figures, claims and PDF bytes. Independent live-model runs previously matched the financial results, but their wording differed.

## Source issues and judgment calls

Allocation history says the target is $515M; the flash says $501.25M. Every earlier target was revised too, including 4Q25 from $496M to $512M. Two historical NAV points changed. V2 flags the differences against the prior report. The chart retains the history and the text uses the flash; I did not silently choose one.

All seven market-chart images match the original 4Q25 package. The latest quarter-labelled observations are 4Q25. The report now labels this as lagged evidence rather than new 1Q26 data.

Tidewater was dissolved. Its notice presents no quarterly percentages, while the flash supplies 5.25%. The report explains both and flags the difference. I keep Tidewater among the 14 flash-carried holdings, not as a claim that all 14 are active.

Silverline's individual LTV is 50.8%, above the numeric 50% Strategic sleeve threshold. The sleeve is at 34.2%, so SPEC's formal compliance test passes. The report separates that result from the individual fund risk.


Cornerstone's funded balance rose $560,000 versus the original package with no recorded contribution. That equals its distribution. I cannot explain it; it is a cross-package finding, not an automated report warning. Beacon Hill's PM approval passes SPEC's four filters, and the prior report also includes PM-approved Ridgeline. Kestrel has no manager report, so I invent no drivers. Northgate and Ridgeline's new funding is now explicit.

## What remains

The draft passes 62 of 63 financial checks. Missing IRR, missing multiple and the target conflict still block approval. Chart readings and model-written commentary need human review. I tested on macOS/Python 3.12, not Windows. I used AI coding tools to help implement and review the code, and I am happy to walk through these decisions. V1 and the supplied inputs remain unchanged.
