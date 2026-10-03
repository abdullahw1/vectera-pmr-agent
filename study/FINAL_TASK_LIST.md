# Final Coding Task List

Planning snapshot from October 2, 2026. The implementation has since been completed and verified locally. See IMPLEMENTATION_STATUS.md for the current checked task list, observed results, deliberate scope reductions, and remaining human release steps. The unchecked items below preserve the original plan, not the current status.

## Done: Keep These Foundations

- [x] Client/quarter CLI and content-based discovery handle the supplied decoys.
- [x] Label/grouped-header parsing and distinction between sleeve headings/subtotals.
- [x] Deterministic contribution formula, role ranking with overlap, committee chronology, compliance.
- [x] Read supplied TWR/IRR and weighted LTV; don't calculate returns with an LLM.
- [x] Preserve blank returns as unavailable and limited blank capital flows as zero.
- [x] Source locators, calculation-input IDs, reconciliation checks, warning/blocker taxonomy.
- [x] Source-verified quotation selection and no invented Meridian asset drivers.
- [x] Existing browser chart correction/confirmation and hash-bound finalization.
- [x] Provider time budget, safe no-key path, pinned OpenAI snapshot, temperature zero, content-addressed cache.
- [x] Local tests and scoped mutations; independent no-key process comparison.
- [x] ReportLab report, extracted prior typography/primary color, supplied flash appendix.
- [x] One-command native launcher implementation; observed Windows run still pending.
- [x] Audit Claude's suggestions against actual sources; record corrections in REQUIREMENTS_AUDIT.md.

## P0: Required Correctness and Acceptance Fixes First

### A. Exact Money and Numeric Provenance: Estimate 2-3 Hours

- [ ] Replace float monetary arithmetic with Decimal/integer cents across ingest, finance, derived totals, evidence serialization, and rendering boundaries.
- [ ] Preserve raw source precision; make source-cent monetary identities exact. Remove the blanket two-cent pass allowance for authoritative additive monetary checks.
- [ ] Separate precision-aware supporting-document/percentage checks from exact workbook money checks.
- [ ] Validate finite values, units, blanks versus zeros, unexpected precision, and boolean-as-number rejection.
- [ ] Create typed numeric facts: entity, metric, period, unit, source locator, authority, precision, and permitted formatted representations.
- [ ] Validate every material printed numeric claim against scoped evidence/derivation. Do not accept a number merely because it occurs somewhere in the facts bundle.
- [ ] Keep financial/role sentences templated; prevent model quotations from changing the numerical inventory unnoticed.
- [ ] Add focused tests for one-cent disagreement, formatting, wrong entity/period, missing values, and source-preserving serialization.

Acceptance: exact active-portfolio monetary identities pass on valid source cents; any unexplained cent difference blocks finalization; legitimate display rounding is explicit and never overwrites source values.

### B. Image Evidence and Meaningful Repeatability: Estimate 2-3 Hours

- [ ] Centralize extraction/correction validation for complete labels, series identity, units, finite values, duplicates, uncertainty, and source locators.
- [ ] Support charts without data labels, including slide 6, through automatically extracted axis-read observations with explicit precision/uncertainty and required confirmation. Investigate deterministic pixel measurement only if scoped and quickly testable; don't build general computer vision under the deadline.
- [ ] Block unsupported/unreadable readings rather than guess. No manual transcription into runtime constants/config.
- [ ] Compute cap-rate spreads/directions from validated data in Python, not model wording or last-quarter prose.
- [ ] Replace model-picked highlights and first-three-only presentation with stable documented chart relevance/presentation rules.
- [ ] Build a canonical semantic manifest: reported numerical claims, all chart data, selected funds/order/roles, compliance, and section structure.
- [ ] Make fresh-run comparison fail when any meaningful figure changes. Keep operational timestamps/agent action order out of the semantic signature.
- [ ] Separate cold provider runs, warm cache reuse, and source/config-bound reviewed replay; do not call replay a cold-run guarantee.
- [ ] Add tests that a changed chart number or quotation number fails despite unchanged financial totals.

Acceptance: mocked tests establish comparison/schema behavior. Real chart accuracy and independent live repeatability remain separate acceptance checks; unresolved variability cannot be marked PASS.

### C. Discovery, Cross-Source Checks, and Coverage: Estimate 1.5-2.5 Hours

- [ ] Record every accepted/ignored/failed file and reason; use consistent source-root-relative paths and explicit ambiguity detection.
- [ ] Cross-check flash identity, benchmark code, and input-derived prior abbreviation; accept the requested client's code/full name in committee rows conservatively.
- [ ] Surface invalid relevant IC dates; match reversals conservatively across normalized prior identities; handle multi-year logs.
- [ ] Keep rules-based entity resolution, reject canonical collisions, and apply it consistently across appropriate source lookups.
- [ ] Compare manager statistics to flash and one-pager commitment amounts to IC with metric/period/precision-aware authority rules.
- [ ] Compare allocation-history requested-period figures to flash at declared USD-million precision and record its client-ownership assumption.
- [ ] Compare prior ending/current beginning where available and definition-consistent. Never demand exact equality from rounded prior prose or from a stub workbook.
- [ ] Record the realized-only $0.51 source discrepancy as an out-of-scope warning, not an active-portfolio blocker.
- [ ] Audit evidence coverage for each material figure/claim, count, rank, and absence statement; improve table-cell references where practical.

Acceptance: discrepancies are explained or surfaced with both locators; authoritative flash values are not averaged with rounded manager statements; all load-bearing ambiguity blocks approval.

## P1: One Agent and a Small SRE Demonstration

### D. Bounded Evidence Agent and Run Diagnostics: Estimate 2-3 Hours

- [ ] Add one explicit action-observation-decision loop over registered source IDs: list evidence, search scoped passages, inspect passage, validate evidence references, finish/escalate.
- [ ] Replace redundant one-shot quotation selection without changing deterministic financial authority.
- [ ] Validate tool arguments; reject fabricated IDs, arbitrary paths, financial overrides, and unbounded repeated actions. Use a global action/time limit and no-key fallback.
- [ ] Keep report claim selection/numerical content under deterministic acceptance; agent execution path can vary but required report meaning cannot.
- [ ] Emit an agent trace of actions, observations, validators, and stop reason; no private chain-of-thought.
- [ ] Add a compact Run Diagnostics section to existing review: stage status/duration, API calls/token usage, cache hits/misses, retries, blocker counts, and agent timeline.
- [ ] Persist structured telemetry and redact credentials. Show actual metrics only; do not label unmeasured values zero or invent success rates.
- [ ] Test feedback-dependent action choice, fabricated evidence, missing support, loop limits, provider failure, and unchanged financial output.

Acceptance: a reviewer can see an actual model-directed tool sequence and why it stopped. No extra framework, vector database, second agent, hosted monitoring, or dashboard rebuild is required.

## P0/P1: Prove and Ship

### E. Hidden-Test Rehearsal and Review Integrity: Estimate 1.5-2.5 Hours

- [ ] Build a coherent synthetic different-client 1Q26 package in a disposable folder, with updated source identities/periods/policies, added and removed holdings, moved rows, and a 2025 approval still open through a 2026 log.
- [ ] Run the full pipeline without production code edits, not only the finance helper. Record expected outputs and observed checks.
- [ ] Add malformed/empty sources, duplicates, missing support, unknown IC action, provider failure, and changed chart source/asset cases; export a compact expected-versus-observed matrix.
- [ ] Require backend review acknowledgment; revalidate structured corrections and source/draft/asset integrity on approval.
- [ ] Keep financial corrections in authoritative inputs; chart correction records include original, changed value, reviewer, reason, and evidence.
- [ ] Export review summary from the existing issue ledger. Optional CLI approval reuses the same validator; no unrestricted overrides.yaml.
- [ ] Run relevant tests and refresh test-results.xml. Arrange observed Windows/launcher evidence separately.

Acceptance: within-contract alternate inputs complete without source edits; invalid inputs never become an unexplained approved report; no mocked test is described as real vision accuracy.

### F. Visual Fidelity, Documentation, Packaging: Estimate 1-1.5 Hours

- [ ] Reuse inspected prior color tokens consistently for text, tables, and charts; preserve readable layout. Chart-vector embedding is optional after acceptance-critical items.
- [ ] Re-render/inspect representative pages and the final PDF; no clipped text or unreadable evidence tables.
- [ ] Correct sample/spec discussion: distinguish genuine role/table issues from terminology, different measures, and allowed appendix choices.
- [ ] Update the two-page write-up, run instructions, architecture diagram, and demo narrative to match implemented behavior and actual results.
- [ ] Include final PDF, approval/evidence/semantic manifest, agent trace, diagnostics, and current tests in the ZIP. Keep drafts labelled; fail packaging's final mode if required approved deliverables are missing.
- [ ] Verify no keys, home-repository secrets, environments, cache, or personal study material are packaged.

Acceptance: the package and write-up honestly reflect the final state, and all reported verification corresponds to the packaged code/data revision.

## Schedule and Cut Line

Estimated effort is now approximately 10-15 focused hours because this audit identified correctness gaps missing from the earlier 8-12-hour plan. These are estimates, not promises; tasks overlap, and live-provider failures can change them. Start with A and B, not dashboard cosmetics. Develop tests alongside each change. Complete a thin D agent loop once the numerical acceptance boundary is established; expand its UI only if time remains.

Deadline pressure does not justify false "complete" claims. If time is insufficient, cut optional vector charts, CLI approval, additional trace polish, and extra retrieval sophistication first. Keep exact finance, truthful no-key behavior, source accountability, full-output repeatability checks, essential fixture rehearsal, and safe human finalization. An unresolved chart acceptance issue is disclosed, not hidden.

No new application code has been changed by writing this checklist. Coding begins only on the approved scope; all unchecked items are genuinely outstanding.

## Tomorrow / External Completion Gates

- [ ] Real provider key supplied privately; necessary network/testing permissions approved.
- [ ] Automatically extract all seven chart images; validate and human-confirm readings, including approximate axis-read values.
- [ ] Execute independent fresh live runs and inspect all semantic differences. Resolve or explicitly disclose remaining failures.
- [ ] Observe clean Windows/Python 3.12 installation and one-command launch, through an available machine or authorized CI/repository setup.
- [ ] Measure actual runtime and token usage; verify the report budget.
- [ ] Abdullah reviews and approves the final report; refresh write-up/package after these results.
- [ ] Rehearse a three-minute demo and spend 60-90 minutes understanding the agent, financial boundary, evidence graph, repeatability, and limitations.
