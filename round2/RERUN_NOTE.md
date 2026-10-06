# CPERS 1Q26 Rerun Note

Abdullah Waheed

## What happened in v1

I froze the evaluated submission at commit 618b990 (tag: v1-submission). I ran it twice, unchanged, against the supplied CPERS / 1Q26 inputs. File discovery worked. Both runs stopped at ReturnsMultiples(Agg)/V28, before any model calls, and produced no PDF. That cell is the Vectera Initiated Investments total's net IRR. Its net multiple at W28 is also blank. The separate CPERS total row and supplied flash PDF have the same gaps. My code accepted missing fund-level returns but assumed these aggregate figures were always present. The report also formatted them directly as numbers. My tests missed that boundary.

## The small v2 fix and checks

I changed two production files. V2 uses the existing missing-value path for aggregate IRR and multiple, records their source cells, and displays "not available" in the overview and table. Missing required figures block final approval; they are not zero or estimates. Six new tests cover either figure missing, both missing, real zero, moved rows/renamed files, and malformed text. All 167 tests passed. Fresh no-key 4Q25 drafts from v1 and v2 were byte-identical. Two fresh live OpenAI 1Q26 runs matched figures, fund roles, approvals, compliance, chart observations, and structure; prose wording differed. V2 produces a 15-page draft with $539.8M committed or approved. It passes 62 of 63 checks, but is not approved for release.

## Conflicting source history

Continuing past the original failure exposed another blocker: allocation history shows a $515M target for 1Q26, versus $501.25M in the flash. The revisions extend backwards. All eight overlapping target points changed, including 3Q25 from $489M to $510M and 4Q25 from $496M to $512M. Historical NAV changed in 2Q25 and 3Q25 too. The prior PMR reports 4Q25 NAV of $436.1M at 88.0% of target, which does not support a $512M target. I cannot tell whether the revisions were intentional. The blocked draft retains the supplied history chart alongside the flash-based target sentence. I did not silently replace either source. The current check catches the requested-quarter conflict, not earlier revisions.

## Judgment calls and remaining gaps

I count 17 positions: 14 carried in the flash plus three open approvals, following SPEC's rule. This is not an active-fund count. Tidewater remains in the flash at zero NAV, but its manager notice and IC monitoring entry confirm termination. That status is omitted because manager prose is displayed only for ranked funds: found, not fixed. I include Beacon Hill's $30M approval despite its PM committee label because it passes SPEC's four explicit filters; I did not add a fifth committee filter. Kestrel has no manager report, so no drivers are invented.

Other same-shaped risks remain in strict aggregate readers, numeric chart formatting, and missing fund-return source references. I kept v2 narrow rather than rebuild those paths. Chart readings and prose still need human review. These runs used macOS and Python 3.12, not Windows. V1 and the supplied inputs remain unchanged.
