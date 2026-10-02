# Requirements Audit and Claude Suggestions

Checked: October 2, 2026. This is a code-and-source inspection, not a new live API or Windows test. The latest previously observed local suite passed 23 tests; the current generated verification artifact records 51/51 financial checks. No new application functionality was implemented during this audit.

Status vocabulary: **Implemented** means present in code with the stated scope, not guaranteed correct for every future input. **Partial** means important gaps remain. **Planned** means not implemented. **Verified locally** excludes real-provider and Windows claims unless stated otherwise.

## 1. Numerical Fidelity: Partial, Highest Priority

### What exists

- Python, not the LLM, reads financial workbook values, calculates quarterly contribution, selects fund roles, filters committee events, and checks compliance.
- Per-fund roll-forward and cross-sheet NAV, sleeve and portfolio additive totals, commitments, and diversification checks are recorded in the ledger. Failed checks block approval.
- TWR, IRR, and weighted sleeve LTV are read from designated source rows; code does not average ratios or ask a model to compute returns.
- Financial sentences and attribution tables are templated from the financial model. Source numbers are never modified just to make a reconciliation pass.

### What does not exist yet

- Exact monetary arithmetic throughout. Ingest converts workbook numbers to floats. Decimal is currently used for display rounding only. Reconciliation currently permits a two-cent difference.
- A context-aware numeric-claim firewall. A verified quotation can contain a source number that differs from the authoritative flash or belongs to another definition.
- Full chart correctness validation. Current vision validation primarily checks nonempty series and finite numeric values, not units, complete labels, axes, or uncertainty.
- An independently validated claim that all report figures are correct. Passing the existing checks does not prove every printed field or image reading.

### Required change

Use Decimal or integer cents for monetary extraction, arithmetic, and serialization, preserving raw source precision and checking unexpected precision explicitly. Require exact equality for additive monetary identities at the declared source-cent precision. Validate finiteness and reject boolean values in numeric fields. For genuinely rounded supporting evidence, use a separate precision-aware comparison with a recorded interval and difference, not a blanket tolerance on authoritative workbook totals.

Keep exact source values distinct from display formatting. A headline such as $436.1M is legitimately rounded for readability; the underlying value and cent-level table remain exact and traceable. Rates often have long source decimals and divisions can require rounding; preserve supplied rates and apply an explicit presentation policy rather than claiming all math can be unrounded forever. Do not recompute TWR/IRR.

No software design can honestly guarantee that an LLM never misreads a chart. Restrict its authority, validate outputs, block unresolved discrepancies, and verify real runs. The workbook financial path must not depend on that probabilistic result.

## 2. Faithfulness: Implemented Core, Partial Coverage

- Manager passages are automatically extracted. Model-selected quotations must occur exactly in the provided source excerpt, whose file and page are assigned by code.
- The model does not supply asset-level explanations for Meridian when its manager report is absent. Its flash-derived role and figures remain present, with a warning and explicit limited-commentary wording.
- Current strategy descriptions come from the relevant one-pagers, not memory or web research.
- The current system mainly uses extractive passages and templated prose, not free-form LLM driver paragraphs. This is deliberately narrower than Claude's proposed generation table.

Improve: validate entity, period, metric, and numeric context of quotations; keep passage IDs and page attribution software-owned; reject fabricated IDs; audit prior-report carry-forward so current facts are never inherited accidentally. Source presence alone does not establish relevance or resolve conflicting source numbers.

## 3. Auditability: Implemented Ledger, Partial Claim Coverage

Facts have file plus cell/sheet, page, or slide/chart locators. Calculations include formulas and input fact IDs. Report paragraphs/tables/charts carry evidence lists; review recursively follows calculation inputs. Evidence JSON and draft JSON are machine-readable.

Gaps: citations are currently block/table level rather than each displayed cell or decomposed claim. Some templated counts, role implications, absence statements, and static connecting statements have broad or empty references. The application does not yet emit an exhaustive accepted/ignored discovery log. An ID may point to a fact graph without a full-path source identifier across duplicate basenames.

Add a coverage check: every material financial output and factual narrative claim must resolve to valid source evidence or an explicit derivation. Record absence as a discovery decision supported by the inspected input inventory. Generate a consolidated manifest/index referencing the existing artifacts, not redundant independent copies. Use source-root-relative paths consistently.

## 4. Human Review: Implemented, Needs Hardening

The browser supports evidence inspection, editing an existing chart extraction, chart confirmation, reviewer acknowledgment, and approval. Approval rejects blockers, stale draft hashes, changed source inputs, and missing chart confirmations; it records a reviewer and final PDF hash. Draft cover/footer labels are present, not a large diagonal watermark.

Financial correction currently means fixing the authoritative workbook and regenerating. Unavailable initial image extraction cannot be replaced by manual transcription. This conforms to the extraction-versus-review distinction.

Gaps: browser acknowledgment is not separately required by the backend; chart correction validation is incomplete; source mutation/finalization deserves stronger automated coverage; generated appendix/image assets need integrity checks too. Local hashes detect accidental changes, not an authenticated or tamper-proof audit system. No CLI approve command, review.md, or overrides.yaml currently exists.

Decision: strengthen the existing workflow instead of adding a second competing approval system. Add an exported review summary if useful. Do not add unrestricted financial overrides. Require structured corrections with original value, source, reviewer, and reason; preserve the initial extraction. Add a simple CLI wrapper only if it reuses the same approval validator and saves meaningful demo time.

## 5. Repeatability: Partial, Acceptance Gap

Financial computation, ranking/tie-breaks, and section assembly are deterministic. The OpenAI default is a snapshot identifier; temperature is zero; the application has provider/model/prompt/image-content-addressed response caching. No-key separate-process runs agree locally.

The standalone verifier currently marks PASS from financial_hash alone, which excludes model chart values. full_report_equal is recorded but does not determine exit status. Prose-selected numbers and model-selected highlight indices can change meaningful content. This is not sufficient for SPEC 1.18.

Change: create a canonical meaningful-result manifest covering every reported number with entity/metric/period/unit, selected funds and order, roles, compliance, and section structure. Compare all validated chart series too, even if a subset is presented. Fail on changed values, not merely changed formatting. Separate independent fresh API runs, warm cache reuse, and reviewed replay. Exclude timings/approval timestamps/action-path order from semantic comparisons.

Caching is not proof of cold-run reproducibility. Agreeing models can still be wrong. Vision remains an acceptance risk until real chart extractions are checked and uncached runs compared. A blocked draft is safer than a wrong final but is not equivalent to satisfying every completion criterion.

Generalization: moved rows/filenames and a finance-only changed-client fixture exist. A complete different-client, 1Q26, multi-year-log report run has not been demonstrated. Add it.

## 6. Robustness: Implemented Cases, Partial Edge Coverage

Current code ignores the supplied decoy flashes by content, chooses a relevant prior report, locates grouped headers dynamically, distinguishes sleeve headings from subtotal rows, normalizes manager names, preserves blank returns, and sorts committee events by date. Unknown action values become blockers.

Gaps: malformed files can abort discovery without a complete classification log; duplicate latest prior reports need explicit ambiguity handling; cross-sheet fund aliases are not handled as broadly as manager-document names; IC filtering recognizes the short code only; relevant rows with invalid dates are silently skipped; reversal-to-prior matching uses a literal name substring; allocation history identity is assumed rather than reconciled. These are targeted fixes, not reasons to build universal document understanding.

## 7. Verification: Implemented Local Suite, More Proof Needed

Existing tests cover golden finance values; inserted rows and renamed filenames; reordered IC logs; bad cash; unknown actions; new zero-balance fund; changed client/policy in the finance layer; future approvals; missing keys; draft tampering; mocked chart approval; quote rejection; API failure/redaction/cache; template readability; environment precedence; and launcher setup reuse/failure behavior.

The Windows/macOS CI workflow exists, but no observed hosted pass is claimed. The real vision provider path and new launcher's full browser flow remain unverified. Saved test-results.xml may predate the latest suite; artifacts must be refreshed after final changes.

Add regression tests for every new guard: exact cents, printed numeric inventory, quote context, missing numeric values, malformed/duplicate sources, full-name IC identity, invalid dates, multi-year approvals, chart uncertainty/schema, source/asset changes, server-side acknowledgment, and all-output repeatability. The rehearsal fixtures must be internally consistent and clearly labelled synthetic, not passed off as actual unseen evaluator inputs.

## 8. Usability and Code Quality: Implemented Foundations

The native one-command launcher installs pinned packages, accepts client/quarter, generates, chooses an available local review port, and opens review. The implementation uses separated modules and an existing API adapter. Comments/docstrings explain non-obvious rules. Documentation discloses no-key/Windows limitations.

Gaps: first setup still needs Python and internet; actual target-machine installation is not proved; browser JSON chart correction is technical; useful operational details are dispersed; the review HTML is a large embedded string. Avoid a frontend-framework rewrite under this deadline. Add small helper modules only where validation is genuinely shared and important.

## Differentiator Decisions

| Suggestion | Current status | Decision and reason |
|---|---|---|
| SRE monitoring/run dashboard | Review shows checks/issues; verification records calls/usage. No stage timings, cache statistics, or agent timeline yet. | Add one compact Run Diagnostics view with structured run ID, stage outcomes/timings, cache hits/misses, API usage, retries, agent action results, and actionable failures. Reuse review UI. No Prometheus/Grafana/hosted service. |
| Verbatim quote plus page | Exact substring check exists; code already owns source page. The model does not return a trusted page number. | Keep and strengthen. Prefer registered passage IDs; code supplies actual file/page and validates scope. Reject invented quotes/IDs, not blindly trust model page metadata. |
| Number firewall | Financial templates exist; global prose firewall does not. | Add scoped numeric provenance validation. Global token membership is insufficient: the right number for the wrong fund/period is wrong. Support legitimate source-backed occupancy, lease terms, dates, and asset names such as Harbor 40; not everything belongs in the flash. Avoid free-form LLM financial prose. |
| Hidden-test rehearsal | Several mutations exist, not the requested full alternate-period package. | High-value core work. Build and run a coherent 1Q26 different-client fixture, altered holdings, moved rows, and approval carried from 2025 into 2026. Include its results matrix. |
| review.md / overrides.yaml / CLI approve | Existing HTML review and approval validator, no YAML override layer. | Export a concise review summary; reuse current corrections/approval controls. No arbitrary financial override file. Large watermark is optional because draft labeling already exists. |
| Cross-document checks | Cross-sheet financial checks exist; manager/one-pager/history comparisons mostly do not. | Add source-authority and precision-aware checks. Compare like-for-like definitions, not every similar label. Use warning versus blocker by relevance and authority. No averaging conflicting sources. |
| Determinism shown | Snapshot/temperature/cache and no-key comparison exist. | Replace financial-only acceptance; publish independent fresh-run scope and observed results. CI compares semantic manifests, not timestamps/full operational traces. |
| Same visual system/vector charts | ReportLab/Helvetica and extracted primary color exist; some tokens differ; workbook charts are PNG. | Fix token fidelity and visually check. Vector chart embedding is optional after core acceptance, not a reason for a new report engine. Don't retype the original flash appendix. |

Priority differentiators: a context-aware number firewall; end-to-end unseen-input rehearsal with intentional failures; one bounded agent with source-scoped tools and visible decisions; a small SRE-style operational summary. These demonstrate skills but no claim is made that competitors lack them or that they guarantee hiring.

## Claude's Fourteen Trap Claims: Checked Against Code and Sources

| # | Claim | Finding and action |
|---|---|---|
| 1 | Two empty decoy flashes and archived stub | Confirmed. Both decoy workbooks say no data; the older PMR is a one-page archive stub. Current discovery handles this via content, not fixed A1/A2 reads. Add explicit accepted/ignored reason records and malformed-file handling. |
| 2 | Full client name must come from prior PMR | Needs correction: SPEC explicitly says the full name and benchmark are in the flash. Current code reads flash identity and infers the short code from benchmark labels. Prior overview does define the abbreviation. Cross-check these and accept code/full-name IC identity, but don't replace the specified flash authority with a mandatory prior-only pattern. |
| 3 | Identical sleeve label means heading or subtotal | Confirmed and implemented using whether the row contains numeric values. Add boundary tests, retaining zero-balance funds. |
| 4 | Blank capital flows versus blank Tidewater returns | Confirmed and implemented semantically. Missing returns render descriptive unavailable text, not 0.00%; add consistent n/m formatting in any numerical table, with source-backed explanation. |
| 5 | Only additive columns foot; realized row differs by $0.51 | Confirmed. Current pipeline avoids adding ratios/vintages and excludes the realized-only row, but does not report its discrepancy. Add an out-of-scope warning with source locator; do not contaminate active portfolio totals or turn that outside-scope issue into their blocker. |
| 6 | Different total return/IRR series | Confirmed. Current summary/compliance follows specified client rows; funded-program since-inception values use the Vectera row consistent with the sample's funded-program wording. Record the explicit choice and relevant ambiguity in the manifest/write-up; don't overwrite differences. |
| 7 | Trailing-space log name, mixed IDs, text amounts, filters | Confirmed and mostly handled. Discovery uses columns, not sheet name; no numeric conversion of IC IDs; regex supports USD20 and USD 25; category/client/date/action filters exist. Invalid relevant dates and full-name clients need fixes. |
| 8 | Ironwood alias, suffixes, numeral variation | Confirmed and manager matching implemented; source extraction can find a full line regardless of its position. A manually maintained alias file is not required by SPEC. Add canonical-collision checks and use controlled matching consistently across sheets/prior activity. Fuzzy suggestions must never silently merge. |
| 9 | Meridian missing manager evidence | Confirmed and handled with flash-only commentary and warning. Exact copying of the prior fallback sentence is not a required fact; our equivalent wording is faithful. Use consistent firm style and improve absence provenance. |
| 10 | Seven chart images, slide 6 unlabelled | Confirmed by source/image inspection. Current prompt excludes unlabelled values, so it cannot cover the whole deck. Add an explicit axis-read mode with precision/uncertainty metadata and mandatory review; never claim an unlabelled pixel estimate is exact underlying data. Do not hand-transcribe image numbers into runtime config. |
| 11 | Prior narrowed office gap versus current widening | Prior wording confirmed; current slide 9 is the office exhibit. Current code does not copy old market prose, but does not compute direction from extracted series. Add spread/direction calculations from validated image facts and check before prose is emitted. The specific current values still need automatic extraction and live verification. |
| 12 | Policy limits from prior, no numeric defaults | Implemented: regex extracts limits and failed extraction creates blockers, not silent defaults. Test alternative supported syntax and conflicting policy matches. |
| 13 | Allocation history has no client field | Confirmed. Current discovery accepts it by headers and report notes rounding, but lacks the cross-check. Match requested-period NAV/target to flash at the history's stated USD-million display precision, log the assumption, and flag mismatch/ambiguity without pretending this conclusively proves ownership. |
| 14 | Home-root Git repo and Python 3.11 | Home-root Git repo confirmed; current project interpreter is already Python 3.12.0. No Git repo is needed for ZIP submission. Never run git add at home root. If using Git/CI, deliberately create/use a project-scoped repository after authorization; never package home .ssh/.aws. |

## Claimed Sample/Spec Disagreements

Prior pages 3-7 were textually reviewed; pages 3, 4, and 7 were also rendered and visually inspected. PDF metadata identifies ReportLab. Source inspection is not a newly approved generated report.

1. **Funded versus committed label:** the sample's Of which funded label is ambiguous/misleading for the commitment amount. Our draft already uses Flash commitment total. Prefer Committed (funded positions), with the distinct Funded Amount clearly defined if shown. Confirm source/metric ownership rather than conflate cumulative paid-in amounts with commitment capacity.
2. **Market versus benchmark comparison:** the sample explicitly carries a disclaimer. SPEC prohibits conflating these series, not necessarily any side-by-side comparison. This is a caution/wording choice, not a proven contradiction. We will keep their identities explicit and use only the custom benchmark for compliance.
3. **Mandate year versus investment inception/vintage:** 2001 appointment, 2011 discretion, and earlier fund/performance dates may represent different things. They are not automatically contradictory. Preserve cited mandate history, explain differing definitions where needed, and flag only a demonstrated ambiguity rather than rewrite dates.
4. **Appendix presentation:** appending the supplied PDF is explicitly allowed. Different rendering is a documented implementation choice, not a sample/spec conflict. Our six-page original appendix explains much of the longer report.
5. **Attribution-role coverage:** a genuine documented issue: the sample's attribution table omits the second-largest position that its prose names. The spec requires each selected role to be explicit. Our report includes all selected roles.

Claude's specific color tokens also require correction. Inspected sample fills yield navy #1B2A4A, stripe #EEF1F6, and gold #C8A24B for common drawn elements. Existing renderer hardcodes some slightly different values. Extract and reuse source colors by role rather than copy unverified hexadecimal guesses. The current workbook charts are raster PNG, not vector.

## Scope Decision

The earlier plan is amended: exact monetary fidelity, all-output repeatability, source integrity, and unlabelled-chart handling come before agent polish. Add one bounded agent, not a multi-agent system. Add lightweight diagnostics, not an observability platform. Add real cross-source checks, not arbitrary override files. Keep new modules small and shared validators explicit.

See FINAL_TASK_LIST.md for the authoritative execution checklist and cut line. Until those items are implemented and tested, they remain planned.

## Primary References

- This workspace's SPEC.md is the authority for financial rules and evaluator requirements.
- The application modules, tests, current draft/evidence/verification artifacts, flash workbook, committee log, allocation workbook, manager PDFs, prior PMR, and retained deck images were inspected for this audit.
- [Python Decimal documentation](https://docs.python.org/3/library/decimal.html) supports decimal arithmetic and explicit rounding behavior; adopting it does not verify our source data.
- [Matplotlib backend documentation](https://matplotlib.org/stable/users/explain/figure/backends.html) distinguishes raster and vector output; the current renderer embeds PNG charts.
