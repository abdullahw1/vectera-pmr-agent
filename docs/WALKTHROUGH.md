# Live Walkthrough Notes

## A five-minute demonstration

1. Run `python -m pmr generate --client CPERS --quarter 4Q25`. Explain that the parameters identify the report, not particular source files.
2. Open `report.pdf`. Show current fund roles, new commitments and reversals. Redwood's role is determined from dollar contribution, not from a manager report's claims.
3. Start `python -m pmr review`. Click a financial paragraph or attribution table; follow a contribution's inputs to income, appreciation and fees cells.
4. Inspect a market image and its extracted values. Explain why a human confirms pixels while numerical portfolio results are computed by code.
5. Show the warning for Meridian's missing manager report. It still has a financial role; the system does not invent assets or a reason for its losses.
6. Show tests for shifted rows, a different client and an additional zero-balance fund. Explain that gold-quarter expectations exist only in tests.

## Explain the business in plain language

- NAV: what the investments are worth now.
- Contribution: how much money a fund's investment performance added or lost this quarter.
- Capital flows: money put into or taken out of a fund, separate from profit.
- TWR: the supplied investment-performance return, adjusted for timing of money moving in/out.
- IRR: the supplied longer-term return measure that also reflects cash-flow timing.
- LTV: debt relative to property value.
- An open approval: an investment authorized by the committee but not funded yet, and not withdrawn or expired.

## Questions you should be ready to answer

**Why not ask an LLM to write the whole report?** The financial outputs must be reproducible and auditable. Code handles math and rules; the model reads ambiguous evidence and chooses verified sentences.

**Why PyMuPDF?** It is an approved parser, reads text and font/layout information, renders review pages, and appends the original flash PDF without external executables.

**How do you prevent hallucinations?** Text is limited to automatically extracted, verifiable passages. Financial prose is templated from source facts. Image readings remain reviewable and require confirmation.

**How do you adapt to another quarter?** Content discovery, dynamic grouped headers, input-derived client policies, chronological committee events, and source-specific adapters. The system relies on the stated file/tab/column contracts, not arbitrary documents.

**What is unfinished?** Be honest about the run you are demonstrating. A no-key report does not include extracted market chart values. Do not describe mocked API tests or the presence of a Windows workflow as actual live API or Windows execution.

**Did you use coding AI?** Yes. Explain which decisions you can defend, how you verified the generated code, and what tests caught. The assignment explicitly allows coding tools.
