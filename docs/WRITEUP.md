# Evidence-Grounded Quarterly Performance Reporting

## Architecture and the AI boundary

The system accepts a client code and reporting quarter, discovers the relevant files by content, and creates a shared report model used by both PDF rendering and evidence review. Python handles workbook extraction, source selection, financial calculations, approval filtering, ranking and compliance. PyMuPDF reads all PDFs and joins the supplied flash appendix. This keeps the implementation portable to Python 3.12 and avoids an office suite, browser PDF renderer or downloaded document models.

Models have two bounded jobs: selecting exact source sentences for commentary and extracting labelled data values from deck images. An API-selected sentence is accepted only if it exists verbatim in the automatically extracted source passage. The report's connecting financial language is deterministic. This sacrifices some stylistic freedom in exchange for strong automatic claim verification: paraphrase entailment cannot be proven by adding a citation or asking another model to approve it. Image readings carry slide/chart locators and remain subject to human confirmation because no source text exists. API calls use OpenAI or Anthropic only; model/provider, prompt and image content determine the cache key.

## Verification and regression detection

The financial layer computes quarterly dollar contribution as income plus appreciation less manager fees. It selects the two positive contributors, two negative detractors and two largest ending positions, retaining overlapping roles. Capital flows are used in roll-forward checks, not attribution. It reads supplied TWR/IRR and weighted sleeve LTV rather than recreating or averaging these measures. Fund-level Ex-US classification and look-through property geography remain distinct.

The pipeline checks fund cash roll-forward, cross-sheet NAV, sleeve/portfolio footing, commitments and diversification totals. It retains exact deltas and a two-cent money tolerance for source rounding. No failed check is repaired by changing a source number. The tests include golden expectations in the test suite only, then change rows, filenames, fund count, client identity, policy and committee chronology. Bad cash values and unknown decisions become blockers. Separate processes with fresh output directories/caches test repeatability; financial values, selection, roles, compliance and structure are deterministic. Model prose selection may vary on uncached runs, as allowed by the SPEC.

## Human review and finalization

The draft PDF is paired with a local evidence review. Selecting a report block opens its source values and recursively follows calculation inputs. Image readings are displayed beside their original chart; a reviewer can correct an existing automatic extraction and confirm it. Financial corrections are made to the authoritative workbook and regenerated, preventing untracked browser overrides. Missing manager evidence permits flash-only commentary and is a warning. Missing required policy or financial sources, reconciliation failures and unavailable image values block finalization. Confirmed charts and a named review acknowledgment are required for finalization.

Approval checks the draft content hash and input-file hashes before producing the final PDF and an approval record that includes the report hash. This prevents an approval from silently applying to changed source inputs. The prototype is a local review tool, not an authenticated multi-user approval system. With no API key, it still generates complete financial results, source-based commentary, all sections and workbook exhibits; numerical market-image enrichment is explicitly unavailable and the report remains a draft.

## Next quarter and format changes

New periods use the same command with different client/quarter parameters. Discovery inspects dates and client identity rather than binding to this package's filenames. Workbook tables are identified by labels and grouped headers, so rows and fund counts can move. Committee logs are discovered by their columns and processed as chronological events across available years; withdrawn/lapsed approvals are excluded from open totals, and prior-reported reversals remain visible in recent activity. Entity matching normalizes punctuation, legal suffixes and Roman numerals, with every match recorded; ambiguous matches are flagged instead of guessed.

Client limits and allocation policy come from the prior PMR, not source constants. The prior PDF also supplies body typography, heading size, primary color and recognizable contents order. Report blocks flow onto extra pages when data grows. A materially new section or unsupported policy syntax is surfaced for review rather than silently inferred. Arbitrary redesign or new financial measures require a new adapter; no claim is made that a prototype can understand every future format automatically.

## Specific judgments and remaining work

Traceability exists as a JSON fact ledger and report-block references, including spreadsheet cells, PDF passages, deck slides/charts, formulas and matching decisions. This quarter, the prior approvals for Alder Creek and Sentinel were withdrawn/lapsed, while Northgate and Ridgeline are current open approvals. Ironwood's III/3/legal-suffix variation resolves under an explicit rule. Meridian is selected despite missing manager evidence. Current market figures are never copied from last quarter's narrative.

The workbook has slightly different portfolio return series; the SPEC-designated FundingStatus/AnnReturns rows own portfolio summary/compliance and annualized charts, while Vectera Initiated Investments owns the funded program's since-inception statistics. The prior report's attribution table omits its second-largest position, although its prose names it; this report's table includes every selected role under SPEC §§1.4-1.5. The six-page original flash appendix is preserved, explaining the longer report rather than compressing exhibits.

Development verification currently covers the no-key path and mocked provider transport; actual API extraction and Windows execution are not claimed as tested. With more time, I would add richer policy adapters, validated numeric-chart bounds, selective paraphrasing with stricter claim decomposition, authenticated review, and broader client/layout fixtures. The immediate completion step is a live API run, human chart confirmation and final Windows installation check.
