# Live Walkthrough Notes

## A five-minute demonstration

1. Run `python -m pmr start`. In New Report, enter `CPERS` / `4Q25` and click Generate Report. Show the real stage progress. Explain that the parameters identify the report, not particular source files. Source Documents can select an unseen document package without code edits.
2. Open `report.pdf`. Show current fund roles, new commitments and reversals. Redwood's role is determined from dollar contribution, not from a manager report's claims.
3. Select the completed run's Evidence Review. Click a financial paragraph or attribution table; follow a contribution's inputs to income, appreciation and fees cells. Runs retains earlier drafts; Audit Bundle exports report and evidence without keys or private logs.
4. Inspect a market image and its extracted values. Explain why a human confirms pixels while numerical portfolio results are computed by code.
5. Show the warning for Meridian's missing manager report. It still has a financial role; the system does not invent assets or a reason for its losses.
6. Expand Run Diagnostics. Show the real agent's list/search/inspect/validate/finish sequence, stage timings and cache counters. Explain the eight-action limit and that it has no money-editing or approval tools.
7. Show `live_repeatability.json`: both fresh API runs must have complete chart data, no blockers and matching canonical semantics on the same code revision. Provider wording can differ; required figures cannot.
8. Show `unseen_rehearsal.json`: a different client and quarter, one holding removed, two added, shifted rows and an approval carried from 2025 into a 2026 log. Golden expectations exist only in fixture/tests.

## Explain the business in plain language

- NAV: what the investments are worth now.
- Contribution: how much money a fund's investment performance added or lost this quarter.
- Capital flows: money put into or taken out of a fund, separate from profit.
- TWR: the supplied investment-performance return, adjusted for timing of money moving in/out.
- IRR: the supplied longer-term return measure that also reflects cash-flow timing.
- LTV: debt relative to property value.
- An open approval: an investment authorized by the committee but not funded yet, and not withdrawn or expired.

## Questions you should be ready to answer

**Why not ask an LLM to write the whole report?** Code owns money, math, rules and financial templates. Source-extractive commentary fixes the numerical inventory. The model investigates registered passages and reads chart pixels; it does not calculate portfolio results.

**What makes this an agent?** A model chooses tools, sees their outputs/errors, and chooses the next action. Read `agent.py`: the action/observation loop and validator are the defining parts, not a framework import. It is a bounded investigator inside a hybrid reporting workflow, not an autonomous analyst.

**Why no LangGraph or vector database?** A small source set needs controlled retrieval and a testable loop. More orchestration would add setup without improving the financial authority boundary. In the real company, this retrieval interface would use their shared RAG service instead of creating a competing engine.

**Why PyMuPDF?** It is an approved parser, reads text and font/layout information, renders review pages, and places original flash content as sharp vector panels without external executables. Oversized source pages are normalized to Letter paper; wide tables repeat investment names instead of shrinking to unreadable text.

**How do you prevent hallucinations?** Text is limited to automatically extracted, verifiable passages. Financial prose is templated from source facts. Image readings remain reviewable and require confirmation.

**Is every figure exact?** Authoritative flash currency identities are cent-exact with Decimal and zero tolerance. Display rounding is explicit. Rounded manager statistics have declared precision; unlabeled chart pixels are approximate and marked `~`. Never describe vision estimates as exact source data.

**How do you adapt to another quarter?** Content discovery, dynamic grouped headers, input-derived client policies, chronological committee events, and source-specific adapters. The system relies on the stated file/tab/column contracts, not arbitrary documents.

**What is unfinished?** Actual Windows interactive/bootstrap verification and Abdullah's chart confirmation/approval are separate gates. Live API access was tested on macOS. Mocked tests do not establish vision accuracy, and two successful cold runs do not guarantee all future provider responses are deterministic. No-key mode has correct finance but unavailable chart numbers.

**Did you use coding AI?** Yes. Explain which decisions you can defend, how you verified the generated code, and what tests caught. The assignment explicitly allows coding tools.

**Were random inputs tested?** Ten fixed-seed cases randomize workbook row offsets, filenames, IC order and selected cash-value corruptions. Valid permutations retain results; unbalanced money changes must block. This is constrained, reproducible adversarial testing, not unrestricted fuzzing or proof that arbitrary layouts work.
