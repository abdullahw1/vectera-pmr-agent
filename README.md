# Submission Quick Start

Implementation instructions are in **[RUNNING.md](RUNNING.md)**. The original assignment follows below.

```powershell
.\start.cmd
```

The launcher installs pinned dependencies on first use and opens the local browser workspace on an available port. In **New Report**, enter the client and quarter, then select **Generate Report**. **Source Documents** accepts another local folder or a folder upload. **Runs** keeps separate reports, progress, evidence review, PDF previews and audit downloads. Requires Python 3.12 with the Windows `py` launcher; first-time setup needs internet access. On macOS/Linux: `python3.12 scripts/launch.py`. Manual setup remains available in RUNNING.md.

The submitted example is `output/report.pdf`; browser-generated drafts are isolated in `output/runs/<run-id>/`. The two-page rationale is `output/writeup.pdf`. Live chart extraction and independent semantic repeatability were tested. Human confirmation/approval and an observed Windows interactive run remain explicit completion gates. See RUNNING.md for the evidence agent, diagnostics and regression results.

---

# Engineering Assignment — Automated Quarterly Report Generation

## Background

For this exercise, Vectera Advisors is cast as a real-estate investment advisor managing private
real-estate portfolios on behalf of institutional clients. Each quarter, for every client,
Vectera produces a **Performance Measurement Report (PMR)** — a polished, ~10–15 page document that
summarizes the portfolio's performance, activity, market context, allocation, and compliance.

Today this report is assembled largely by hand from a set of quarterly inputs. **Your task is to
build an agent that generates the PMR automatically** from those inputs, matching the format and
quality of the prior quarter's report.

All data in this package is **synthetic**. Cascadia Public Employees' Retirement System ("CPERS")
is a fictional client; all funds, figures, and names are invented for this exercise.

## The task

Build a system (an "agent") that takes the **Quarter 4 2025 (4Q25)** inputs below and produces the
**4Q25 PMR** for CPERS — a document that mirrors the structure, tone, exhibits, and numerical
content of the provided prior-quarter report.

> **You are not expected to be a real-estate finance expert.** The financial rules you need — how to
> identify the funds that moved the portfolio, how new commitments are handled, what must reconcile,
> and the compliance checks — are specified in **[`SPEC.md`](SPEC.md)**, along with what we evaluate
> and what to submit. Read the prior PMR as the worked example and `SPEC.md` as the rulebook.

Every submission is run the same way, regardless of implementation: a person tells your system **which
client** and **which reporting quarter** to generate, and nothing else. From that starting point, your
system finds and reads the right files itself. See `SPEC.md` §1.20.

Two tooling constraints apply so we can consistently run and re-test every submission: PDF parsing is
limited to **docling, PyMuPDF, or pdfplumber**, and LLM calls are limited to the **Claude or OpenAI
API**. Read any API key from `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` — don't hardcode one, and don't
fail if it's absent. If model access is a barrier for you, tell us before you start and we will sort
it out. See `SPEC.md` §1.21 for the specifics. Within those bounds, which library and which model you reach for — and why — is yours to
decide.

## What you are given (`inputs/`)

The folder is a shared drop location, not a curated bundle — it may contain files for other quarters
or other Vectera clients that have nothing to do with this report. Figuring out which files are
actually relevant to the CPERS 4Q25 PMR is part of the task, not a data-quality problem to work around.

| File | What it is |
|---|---|
| `prior_pmr_3Q25.pdf` | **Last quarter's finished PMR.** This is your template for format, tone, section structure, and exhibits — and your baseline for any quarter-over-quarter comparison. |
| `flash_4Q25.xlsx` | The **quarterly portfolio data dump** ("flash"). Multi-tab workbook: funding status, returns & multiples, cash activity, annual returns, geographic and property-type diversification. This is the source of truth for all portfolio numbers. |
| `flash_4Q25.pdf` | The same flash **rendered as a PDF** — a readable exhibit you can use for the report's appendix. |
| `manager_reports/*.pdf` | **Quarterly reports from individual fund managers.** More reports are supplied than the report needs, and — separately — not every fund the report needs will necessarily have a report supplied. Selecting the right funds to feature (e.g. the most material contributors, detractors, positions) is part of the task, and so is handling a fund that has no manager report at all without inventing what it would have said. Some of the reports are short **strategy one-pagers for newly approved commitments** — see the note on new commitments below. |
| `market_outlook_4Q25.pptx` | Vectera's **house-view market outlook** deck. The report's Market Update section should be a concise, portfolio-relevant condensation of this. Its charts are images, not editable chart data. |
| `ic_log_2025.xlsx` | The firm-wide **Investment Committee log** of commitment approvals across *all* Vectera clients. The report's Recent Investment Activity section should reflect this client's approvals for the period. |
| `allocation_history.xlsx` | Historical target-allocation vs. net-asset-value series, for the allocation-over-time exhibit. |

You should not assume every file in the folder shares this naming pattern, belongs to this client, or
belongs to this quarter.

## The deliverable

1. **Working code** for your agent (any language/stack), with instructions to run it.
2. **The generated 4Q25 PMR** it produces (PDF and/or Word).
3. **Your tests / verification** — whatever gives you confidence the output is correct.
4. A short **write-up** (1–2 pages). See [`SPEC.md`](SPEC.md) Part 3 for the full list of what it
   should address — including how you keep outputs grounded and auditable, where a human reviews and
   approves, how you verify correctness, and how it adapts to the next quarter and to reasonable
   changes in the report's format.

## What a strong solution demonstrates

- **Correct fund selection, framed by role.** The report identifies and writes up the funds that
  materially moved the portfolio — the **largest contributors and detractors to quarterly performance,
  and the largest positions** — derived from the portfolio data (not simply every fund a manager report
  happens to exist for). Each featured fund's commentary should make its role explicit (e.g. "was the
  Portfolio's largest contributor…"), as the prior-quarter sample illustrates.
- **Numerical fidelity.** Every figure in the report reconciles to the flash data. Portfolio,
  sleeve, and fund numbers foot; nothing is invented.
- **Faithful narrative.** Fund commentary is grounded in the manager reports; the market update
  reflects the outlook deck; recent activity reflects this client's IC-log approvals. No
  hallucinated facts — including where a manager report simply isn't available for a fund that matters.
- **Format & tone match** the prior PMR — not just section structure and voice, but the visual system:
  color palette, typography, and table styling.
- **Exhibits.** The performance, allocation, diversification, and returns charts are reproduced from
  the correct data, including values pulled from the outlook deck's chart *images*.
- **Quarter-over-quarter awareness.** Where the prior report informs the current one, it is used.
- **Judgment under ambiguity.** The inputs are realistic and imperfect; how you resolve gaps, resolve
  entities that are labeled slightly differently across documents, flag uncertainty, and avoid
  overreach matters.
- **Every fact is automatically extracted, not hand-entered.** If a number or claim required a person
  to read a source and type it into your system rather than your system reading the source, that's a
  gap, not a shortcut.
- **It survives being run again, and run on a different quarter.** Two runs on the same inputs produce
  the same report. Pointing it at a different reporting period's inputs works without touching the code.
  We will test this directly: your submitted system will be run against a second, unseen input set for
  a different reporting period — possibly for a different client — with no code edits.
- **Repeatability is critical, and hardcoding is a rejection.** The input workbooks from one period to
  the next will be **similar but are not guaranteed to have the same structure** — expect the same
  files, the same sheet names and the same column meanings, but **not** necessarily the same number of
  funds, the same rows, or the same layout. Funds get added, wound down, or moved, so headings and
  totals can sit at different positions. Find what you need by reading labels and headers, never by
  fixed cell coordinates. Any figure, fund name, row number, filename, fund count or ranking written
  into your source code rather than read from the inputs fails this requirement — even if this
  quarter's output happens to be correct. See `SPEC.md` §1.18.

## Notes

- **New commitments (approved this quarter, not yet closed).** Some of the manager documents are
  strategy/overview one-pagers for commitments the Investment Committee approved during the quarter
  (see `ic_log_2025.xlsx`) that had **not closed or funded by quarter-end**. Because they are
  unfunded, such commitments do **not** appear in the flash and carry no performance figures. They
  belong in the **Recent Investment Activity** section as the quarter's new commitments — not in the
  performance commentary as funded holdings. Identifying which approvals qualify is part of the task.
  The commitment facts (fund, amount, date) come from the IC log; the one-pagers add strategy color.
- **`SPEC.md` is the rulebook; the prior PMR is the worked example of the output.** The financial
  rules are handed to you in `SPEC.md` — you are not expected to reverse-engineer them. Use the prior
  PMR for what a finished report looks like: structure, tone, exhibits, and the visual system. Where
  the two ever appear to disagree, **`SPEC.md` wins** — tell us in your write-up where you saw the
  conflict.
- There is no single "framework" you must use. We care about correctness, judgment, code quality,
  and how you reason about an underspecified, high-stakes document-generation problem.
- **There is no fixed hour budget.** We are evaluating whether you can recognize what *finished*
  means for a client-facing report: every figure reconciles to the source, the format matches the
  prior quarter, and the process re-runs on new inputs without code changes. Submit when it meets
  that bar — and tell us what you deliberately left out, and why. A focused, well-reasoned partial
  solution with a clear write-up is preferred over an over-engineered one.
- **Please return your submission within 4 calendar days of receiving this package.**
