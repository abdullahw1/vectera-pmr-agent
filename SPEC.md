# Specification & Evaluation Criteria

**You are not expected to be a real-estate finance expert.** This document hands you the financial
rules you need to implement (Part 1) and tells you what we actually evaluate (Part 2) and what to
submit (Part 3). Read the **prior PMR** (`inputs/prior_pmr_3Q25.pdf`) as the worked example, and use
this document as the rulebook. We provide the domain knowledge on purpose — we want to see your
**engineering**, not your familiarity with real estate.

---

## Part 1 — Financial body of knowledge (the rules to implement)

The PMR turns a set of quarterly inputs into a polished report. Here is everything you need to know
about the domain to do that correctly.

### 1.0 Glossary — vocabulary, not expertise
None of this requires prior real-estate or private-equity experience. These are one-line definitions
so unfamiliar vocabulary doesn't cost you time; the engineering test is whether you can turn the rules
and formulas in this document into correct code, not whether you'd already seen these terms.

- **NAV (net asset value)** — the current market value of the portfolio (or a fund, or a sleeve).
- **TWR (time-weighted return)** — a performance return that strips out the effect of *when* money was
  added or withdrawn, so it measures how well the investments themselves performed. Used for quarterly
  and trailing-period (1/3/5/10-year) returns.
- **IRR (internal rate of return)** — a performance return that *is* sensitive to the size and timing of
  cash flows. Used for the since-inception track record.
- **Net equity multiple** — total value created (capital returned + current value) divided by capital
  invested, expressed as a multiple (e.g. 1.45x means $1.45 back for every $1 invested, so far).
- **Both TWR and IRR are already calculated for you in the flash** (§1.3, §1.9 below say exactly where)
  — you read and roll these up, you do not derive them from raw cash flows. The disclosure boilerplate
  in the prior PMR mentions the methodology ("Modified Dietz") used to originally produce these numbers;
  that's disclosure language to reproduce verbatim, not a calculation to implement.
- **LTV (loan-to-value)** — the fund's debt as a percentage of its property value; higher means more
  leverage. Also already pre-computed in the flash (§1.9).
- **NOI (net operating income)** — a property's rental income after operating costs, before financing
  and capital spending. Appears in the market outlook deck as a forecast metric; you don't compute it,
  you report the deck's forecast.
- **Cap rate (capitalization rate)** — a property's NOI divided by its value, used as a market pricing
  signal. Cap rates and property values move **inversely**: a falling/compressing cap rate means rising
  values; a rising/widening cap rate means falling values. This matters if your Market Update narrative
  characterizes a cap-rate move — getting the direction backwards is a factual error, not a style choice.
- **Basis points (bps)** — hundredths of a percentage point; 100 bps = 1%. "Outperformed by 50 bps"
  means "outperformed by 0.50 percentage points."
- **Sleeve** — a grouping of funds by strategy (Strategic vs. Tactical/Special Situations); see §1.2.
- **Sector / style labels** you'll see attached to funds and properties — *core, core-plus, value-add,
  opportunistic* (roughly, ascending risk/leverage), *open-end* vs. *closed-end* (evergreen vs.
  fixed-term fund structure), *vintage year* (the year a fund began investing). You don't need to reason
  about what these imply — carry them forward faithfully from wherever they already appear in the
  inputs; they're descriptive labels, not values you calculate.
- **NCREIF / NFI-ODCE / NPI** — real-world industry index names (the client's benchmark is built on
  one of these). Treat them as labels to carry forward exactly as given in the flash/prior PMR, not
  something to understand structurally.

### 1.1 Report structure
Match the section structure of the prior PMR. It contains, in order: portfolio overview & investment
guidelines, fund statistics, portfolio managers, an annualized time-weighted-return (TWR) chart, a
performance update, strategic-portfolio commentary, tactical & special-situations commentary, recent
investment activity, a market update, an allocation-over-time exhibit, property- and geography-type
diversification exhibits, a compliance table, disclosures, and an appendix containing the flash.

### 1.2 Portfolio structure
The portfolio is divided into **two sleeves**: *Strategic* and *Tactical*. Every fund belongs to one
of them; the two sleeves roll up into the total portfolio (labelled **"Vectera Initiated
Investments"** in the flash). Performance is compared against the **CPERS Custom Benchmark** (an
NFI-ODCE-based benchmark). The flash uses these exact labels.

For historical reasons the report's second commentary section is titled **"Tactical and Special
Situations Portfolio"**. It covers the Tactical sleeve; there is no separate Special Situations
sleeve in the data.

### 1.3 How to identify the funds that "moved" the portfolio (attribution)
For each fund, its **dollar contribution to quarterly performance** is:

> **contribution = income + appreciation − manager fees**  (for the quarter)

All three components are in `flash_4Q25.xlsx`, sheet `CashActivity(Agg)` — columns **Gross Income**,
**Appreciation**, and **Manager Fees**. Rank funds by this **dollar** figure:
- The most positive contributions are the **top contributors**.
- The most negative are the **top detractors**.
- Rank by **dollars, not percentage return** — a small fund with a high % return is not necessarily a
  large contributor.

**Why only these three columns.** `CashActivity(Agg)` has more columns than that — Beginning/Ending
Market Value, Contributions, Distributions, Withdrawals, in addition to Income/Fees/Appreciation. The
full quarterly roll-forward is:

> Beginning MV + Contributions − Distributions − Withdrawals + Gross Income − Manager Fees +
> Appreciation = Ending MV

(this identity is what §1.8's footing check should reproduce, per fund). Contributions, Distributions,
and Withdrawals are **capital flows** — money an investor put in or took out — not investment
*performance*, so they're correctly excluded from the attribution formula above. Only Income,
Appreciation, and Fees reflect how the investment itself performed during the quarter; that's why
attribution uses exactly those three and no others.

The flash also carries **TWR and IRR figures already calculated** for every fund and period
(`ReturnsMultiples(Agg)` for quarterly/1/3/5/10-year, `AnnReturns(Agg)` for the annualized series used
in the TWR chart, and IRR/net-multiple columns alongside them) — you read and roll these up, you do not
derive them from the cash-flow columns.

### 1.4 How many funds to feature — select by rank, not by a dollar threshold
Selection is driven by **rank on the dollar figures in §1.3**, not by an absolute cut-off. For each
quarter, feature:

| Category | How many | Ranked by |
|---|---|---|
| Top **contributors** | the **two** largest | most positive dollar contribution (§1.3) |
| Top **detractors** | the **two** largest | most negative dollar contribution (§1.3) |
| Largest **positions** | the **two** largest | market value at quarter-end |

Do **not** apply a fixed dollar threshold. A quarter's two largest detractors may each be well under
$1M and are still that quarter's two largest detractors. Likewise a fund can post a large percentage
return on a small base and still not rank — rank on dollars (§1.3).

Edge case: if fewer than two funds had a **negative** dollar contribution, feature all those that did
and state explicitly that every other fund contributed positively.

**Scope of this rule.** §1.4 governs the **performance/attribution** selection — which funds earn an
explicit *role* callout ("largest contributor", "largest detractor", "largest individual position").
It does **not** cap the sleeve commentary. The *Strategic Portfolio* and *Tactical and Special
Situations* sections still walk the sleeve's holdings more broadly, as the prior PMR illustrates —
the ranked funds simply get the fuller treatment and the explicit role language.

### 1.5 Which funds to feature
Three important rules:
- **Selection is driven by the flash, not by which manager reports exist.** More manager reports are
  provided than the report needs. A report existing for a fund does **not** mean you feature it.
- **A fund can hold more than one role, and you must state each one.** The three lists in §1.4 overlap:
  the same fund is frequently both a top contributor and a top-two position, or both the largest
  position and a detractor. Such a fund is written up **once**, with **all** of its roles made explicit.
  Do not pad the report to six separate funds — the six slots are typically filled by four.
- For each featured fund, make its **role explicit** in the commentary (e.g. "was the Portfolio's
  largest contributor to performance during the quarter", "is the Portfolio's largest individual
  position"), as the prior PMR illustrates. A reader must be able to tell *why* each fund appears.

### 1.6 New commitments (approved this quarter, not yet closed)
Some funds are **new commitments** the Investment Committee approved during the quarter but which had
**not closed or funded by quarter-end**. Because they are unfunded, they:
- do **not** appear in the flash and have **no** performance figures, and
- belong in the **Recent Investment Activity** section — **not** in the performance commentary.

Their commitment **facts** (fund, amount, date) come from the IC log (§1.7). Feature **every** new
commitment this client's IC approved during the quarter — there is usually more than one, and missing
one is a substantive error. For **each** new commitment, write a brief **1–2 sentence description of
the fund's strategy** drawn from its one-pager (sector, style, and what it will invest in) — the
section should read as informed commentary, not a bare list of names and amounts. **Lead with the
largest new commitment.** Do not invent NAV or returns for these funds. If no commitments were
approved during the quarter, say so explicitly.

**They still count in the "committed or approved" totals.** The portfolio overview states a
since-inception figure for capital *"committed or approved for commitment"* across a number of
*"individual investment positions"*. Both of those **include approvals that have not closed** —
that is what "or approved for commitment" means. So:

- **total committed or approved** = the flash's committed total **plus** every **open** approval
  for this client;
- **number of positions** = the funded investments in the flash **plus** every open approval.

An approval is **open** at quarter-end when all three of these hold: the IC approved it for this
client **on or before quarter-end**, it has not closed or funded (so it is absent from the flash),
and it has **not since been withdrawn or lapsed**. Both the meeting date and the IC log's
**Committee Action** column matter — a `Commitment` row dated after quarter-end is not yet an
approval for this report, and a later row that withdraws or lapses an earlier approval removes it
from both totals. Do not assume every `Commitment` row is a live approval; read the date and the
action. Usually the open approvals turn out to be just the current quarter's, but confirm that
from the log rather than assuming it.

**If a previously reported approval was withdrawn or lapsed this quarter, say so.** The client was
told about that approval in an earlier report, so a report that simply drops it reads as an omission.
Add **one sentence** to Recent Investment Activity naming the fund, the amount and what happened —
for example, "The USD 12 million commitment to Example Growth Fund II approved in March was
withdrawn during the Quarter after the manager postponed its first close." (That wording is an
illustration, not this quarter's answer.) This is not a new commitment and must not be listed as
one; it is a one-line note on the quarter's activity. If nothing was withdrawn or lapsed, say nothing.
Finding these requires comparing the log against what the prior report stated — see §1.12.

State the split rather than leaving it implicit — for example, "…across 14 individual investment
positions: 12 funded and carried in the flash, plus 2 approved during the quarter that had not
closed by quarter-end." Everything else about these funds is unchanged: no NAV, no returns, no
performance commentary, and they appear in Recent Investment Activity only. The prior PMR shows
this treatment in its overview.

### 1.7 The IC log is firm-wide — filter to this client
`ic_log_2025.xlsx` records Investment Committee decisions across **all** of Vectera's clients, of
several kinds, for the whole year. The Recent Investment Activity section must reflect **only this
client's (CPERS)** new commitments **for the reporting quarter**. Four filters apply, and all four
are required:

1. **Decision type** — `Recommendation Category` = `Commitment`. The column also carries
   `Due Diligence`, `Monitoring`, and `Other` rows, which are not new commitments.
2. **Client** — the `Client` column equals **the requested client's short code** (for this report,
   `CPERS` — but take it from the run parameter, not from a constant in your code; see §1.18).
   Other clients appear in the log and must be excluded.
3. **Quarter** — `Meeting Date` falls inside the reporting quarter. Commitments this client approved
   in *earlier* quarters belong to those quarters' activity, not this one's. Some will already appear
   in the flash as funded holdings; others may still be closing and appear nowhere in the flash.
   Either way they are out of scope for this quarter's Recent Investment Activity.
4. **Decision outcome** — `Committee Action` = `approved`. **A `Commitment` row is not automatically
   an approval.** The log also records decisions that *undo* an earlier approval, and those rows carry
   the same category, client and fund as the approval they reverse. The values you will encounter are:

   | `Committee Action` | Meaning | Counts as a new commitment? |
   |---|---|---|
   | `approved` | the commitment was approved | **yes** |
   | `withdrawn` | a previously approved commitment was withdrawn | no |
   | `lapsed` | a previously approved commitment expired unexercised | no |
   | `deferred` | no decision was taken | no |

   If you meet a value that is not in this table, **do not guess** — exclude it from the totals and
   flag it for human review, per the conservative principle in §1.14.

Dropping any one of the four filters produces a wrong answer. Note also that the log is **not sorted
by date** — do not assume row order corresponds to chronology.

**Which log files exist.** The IC log is maintained **one file per calendar year**, named for its year
(`ic_log_2025.xlsx`, `ic_log_2026.xlsx`, …). Discover it by pattern, not by a fixed filename — the
year changes with the reporting period (§1.18). The drop folder will always contain every log file
needed for the reporting period, including an earlier year's log when an approval that is still open
at the reporting date was made in that earlier year.

### 1.8 Reconciliation (footing)
Every figure in the report must tie back to the flash. Fund numbers roll up to sleeve totals, and
sleeves roll up to the portfolio total; those must **foot**. Nothing is invented or estimated.

### 1.9 Compliance
Reproduce the compliance table shown in the prior PMR: guideline, limit, actual, status, for four
checks. Each is computable directly from the flash — here is exactly where each "actual" figure comes
from:

- **Sector concentration** (limit: ≤40% per sector) — the **largest single value** among the
  property-type percentage columns (Apartment, Office, Industrial, Retail, Hotel, Other) in the
  `All Property` sheet's portfolio-total row. Whichever sector is largest, name it — report the
  figure and the sector together, formatted as e.g. `31.4% (Retail)`. That is an illustration of
  the format only — read the actual value and sector from the sheet, and do not assume which sector
  leads, as it can change between quarters.
- **Leverage / LTV** (limits: ≤50% strategic, ≤75% tactical) — `CashActivity(Agg)`'s **LTV** column
  already carries a pre-computed, correctly weighted figure on the **"Strategic Investments"** and
  **"Tactical Investments"** subtotal rows (and on "Vectera Initiated Investments" for the portfolio
  total). Read these directly — **do not** recompute leverage by averaging individual funds' LTV
  percentages; a simple average of ratios is not the same number as the true weighted figure, and the
  flash has already done that weighting correctly for you.
- **Ex-US exposure** (limit: ≤35%) — **read this from `FundingStatus(Agg)`'s "Ex-US Portfolio" row**
  (a fund-level classification: is the fund itself a US or non-US vehicle, weighted by market value).
  **Do not use `All Geographic`'s "Ex-US" column for this check** — that sheet reports a *different*,
  equally legitimate number: the **look-through** percentage of underlying *properties* located outside
  the US, regardless of which fund holds them. The two will not match (a US-domiciled fund can still
  hold some non-US properties), and that is expected, not a data error. Use `FundingStatus(Agg)` for
  the compliance check; use `All Geographic` for the geographic diversification exhibit (§1.1). If your
  report shows both figures anywhere, say explicitly that they measure different things.
- **Return objective** (exceed the benchmark) — compare the portfolio's **1-year net TWR**
  (`FundingStatus(Agg)`'s summary row, "TNET" under "1 Year") against the **CPERS Custom Benchmark's**
  1-year net TWR (`AnnReturns(Agg)`, the benchmark's row, "Net" under "1 Year"). State both and whether
  the portfolio exceeded it.

### 1.10 Market update
The Market Update section is a **concise, portfolio-relevant condensation** of the house-view outlook
deck (`market_outlook_4Q25.pptx`) — not a copy of it. The deck carries both narrative and **data
exhibits (charts)**; a strong Market Update reflects the quantitative signals in those exhibits, not
just the prose. **The deck's charts are images, not editable chart data** — the numbers exist only in
the pixels.

**The deck's market indices are a different series from the client's benchmark, and they will not
agree.** The deck reports broad market returns; the flash reports the **CPERS Custom Benchmark**, a
client-specific series. Where both appear, the figures legitimately differ — that is expected, not a
data error. Do not conflate them, and do not "reconcile" one to the other.

### 1.11 Appendix
The prior PMR ends with the quarterly flash as an appendix exhibit. The flash is provided both as the
data workbook (`flash_4Q25.xlsx`) and as a rendered PDF (`flash_4Q25.pdf`) you can use for the appendix.

### 1.12 Quarter-over-quarter
Treat the prior PMR as both the **format specification** and the **comparison baseline** where the
current report refers to change over the quarter.

### 1.13 Automated ingestion — no manually-transcribed facts
Your system must **parse the supplied files itself**. A material fact (a number, a chart value, a
name, a date) that a human read out of a source document and typed into a config file, a constant, or
a prompt does **not** satisfy this requirement, even if the fact is correct — the point is that the
*software* extracted it, not a person standing in for the software.

This is not the same thing as human **review**. A human inspecting, correcting, or approving a fact
the system already extracted is expected elsewhere (§1.17) and does not violate this rule. The line is:
did a person do the extraction (not allowed), or did a person approve what the system extracted
(required)?

### 1.14 Entity resolution across documents
The same fund or client may appear with slightly different labels across documents — a legal suffix
present in one place and not another, a numeral written as a word or a Roman numeral versus an Arabic
one, an abbreviation, a punctuation difference. Your system must resolve these to a single canonical
entity, and the resolution must be:
- **controlled** — driven by an explicit, inspectable mapping or matching rule, not an opaque model
  guess;
- **traceable** — a reviewer can see why two labels were treated as the same entity (or why they
  weren't); and
- **conservative** — when a match is ambiguous, flag it for human review rather than resolving it
  silently. A wrong merge (treating two different entities as one) is worse than an unresolved case.

### 1.15 Missing supporting evidence
One or more documents this report would normally draw on may be **absent**. Your system must:
- detect the gap rather than silently proceeding as if the document existed;
- continue generating a draft wherever the missing document isn't load-bearing for a required figure
  (the flash alone is always sufficient for a fund's role and dollar figures — see §1.3–§1.5);
- **never invent narrative detail** (asset names, drivers, management commentary) to fill the gap; and
- distinguish a **draft-stage warning** (safe to proceed, flagged for the reviewer) from a
  **finalization blocker** (a required figure genuinely cannot be produced) in whatever the system
  surfaces to a human reviewer.

### 1.16 LLM use: extraction and narrative, not computation
Where extracting or synthesizing information requires judgment — reading a chart image, deciding which
passage of a manager report is the material one, writing the connecting prose — an LLM is the
appropriate tool, and its use is expected. Where the task is **computing, ranking, filtering,
reconciling, or checking compliance**, the answer must be produced by **deterministic code**, not by an
LLM. A number that an LLM computed or transcribed, rather than code, is treated as ungrounded even if
it happens to be correct. If an LLM extracts or paraphrases a claim **from text**, that claim must be
checked against the source passage before it appears in the report — a citation you cannot verify is
not a citation.

**Values read from a chart image are the one case where no source text exists to check against.** We
are not asking for the impossible there. What we expect instead is that the value carries a locator
(which deck slide and which chart it came from — §1.17), and that a human can confirm it before
finalization (§1.15). A plausibility check in code — against the axis range, a total that should sum
to 100%, or a figure the flash reports independently — is a good addition, not a requirement.

### 1.17 Traceability
Every material figure and every factual narrative claim in the output must carry a **machine-readable
source locator** — the specific file, and the sheet/cell, page, or slide it came from. This should be
producible as structured data (e.g., a manifest), not only as prose citations inside the report, so a
reviewer or an automated check can walk every claim back to its evidence.

### 1.18 Reproducibility
Reproducibility is a **pass/fail requirement**, not a matter of degree. Running your system twice, in a
clean environment, on the same inputs must produce the same result. Your system must also run against a
**different reporting period's inputs** — same file/tab/column contracts, different portfolio data —
**without any manual edits or quarter-specific code changes**. A configuration or manifest that your
system itself reads to locate quarter-specific filenames or labels is fine; modifying source code for a
new period is not.

**What "the same result" means.** If you use an LLM for narrative, we do not expect byte-identical
prose on two runs, and we will not fail you for it. What must be identical is everything that carries
meaning: **every figure, the fund selection and ordering, the roles assigned, the compliance results,
and the section structure.** If your prose also comes out identical — because you pin a seed, set
temperature to zero, or cache — say so in your write-up; it makes the check easier, and it counts in
your favour.

**Client-specific values must come from the inputs, not from your source.** The unseen run may be for
a different client. Everything client-specific is present in the package and should be read from it:
the client's full name and the benchmark label are in the flash workbook, and the guideline limits and
the target-allocation policy are stated in the prior PMR's investment-guidelines and compliance
sections. Writing `"CPERS"`, `"CPERS Custom Benchmark"`, `40`, `50`, `75` or `35` into your code as
constants is the same defect as hardcoding a figure.

**We will run this.** After you submit, we will execute your system as-is — same interface, client and
quarter only — against a **second, unseen set of inputs** for a different reporting period, possibly
for a different client, with no code edits of any kind. Whether it completes, and whether its figures
are correct, is part of the evaluation.

**The inputs will be similar, but their exact structure is not guaranteed.** Expect the same files, the
same sheet names and the same column meanings. Do **not** expect the same number of funds, the same
rows, or the same layout — a fund may be added, wound down, or moved, so headings, subtotals and
section boundaries can sit at different positions, and a fund may legitimately appear with a zero
balance. Locate what you need by reading labels and headers, not by fixed cell coordinates.

**Hardcoding is a rejection, not a deduction.** Any figure, fund name, row or cell reference, filename,
fund count or ranking that is written into your source code rather than derived from the inputs fails
this requirement — even if this quarter's output happens to be correct. The distinction we apply: a
*golden test* in your test suite that asserts this quarter's known-good output is good practice and we
want to see it; a check **inside the running pipeline** that expects this quarter's fund names, fund
count, or number of commitments is a defect, because it will simply fail next quarter.

### 1.19 Output format fidelity
The generated report should be visually consistent with the prior PMR, not merely structurally similar
— the same color palette, the same heading and body typography, and the same table styling (header
treatment, row striping, rule placement). A report that gets every number right but doesn't look like
it came from the same firm as last quarter's is not a finished deliverable.

### 1.20 Starting point
Every submission is run the same way: a person specifies **which client** and **which reporting
quarter** to generate a report for, and nothing else. From there, your system is responsible for
locating the correct files in the inputs folder itself — including recognizing and disregarding files
that don't belong to the requested client or quarter. How you build this (a command-line prompt, a
terminal menu, a small web form) is your choice; the interaction contract — client and quarter as the
only inputs — is not.

**Accepted formats.** The client is given as its **short code** (`CPERS`) and the quarter as
`4Q25`-style. Accepting the client's full name as well is fine, but the short code must work. Resolve
the short code to the full name from the inputs (§1.18), not from a table in your source.

### 1.21 Approved tooling
So we can run and re-test every submission consistently:
- **PDF parsing/extraction** must use one or more of: **docling**, **PyMuPDF** (`fitz`), or
  **pdfplumber**. These are the only three permitted libraries for reading the manager reports, the
  prior PMR, and the flash PDF — no other PDF library, local or hosted, may be used.
- **LLM calls** must go to the **Anthropic (Claude) API** or the **OpenAI (GPT) API** only. No other
  model provider, and no locally-hosted or open-weight model, may be used for any part of the pipeline.
  Read any API key from `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`; don't hardcode one, and don't fail
  if it's absent. We do not supply a key by default — if model access is a barrier for you, tell us
  before you start and we will arrange it.

**What "don't fail if it's absent" means.** With no key set, your system should still run end-to-end
and produce a report whose **figures, fund selection, compliance results and structure are complete
and correct** — everything §1.16 says must come from deterministic code. Narrative that genuinely
requires a model may be omitted or clearly marked as unavailable. Say in your write-up which sections
degrade. Exiting with an error because no key was found is a failure of this requirement.

Within those bounds, which specific library and which specific model you reach for — and for what — is
your judgment call, and we're interested in the reasoning behind it.

---

## Part 2 — What we evaluate

We provide the finance (Part 1) so we can focus on your **engineering**. We care about how you build a
**correct, faithful, auditable, repeatable, human-supervised** system over messy, real-world inputs.
In rough priority:

- **Correctness & numerical fidelity.** Every figure in the output reconciles **exactly** to the
  source data; all totals foot. This is the highest bar.
- **Faithfulness to the evidence.** Every fact and every number is derived **solely** from the
  provided inputs. Nothing is invented, inferred beyond the evidence, or hallucinated.
- **Auditability.** A reviewer must be able to trace **any** figure or statement in the output back to
  its source. Traceability is a first-class requirement in this industry, not an afterthought.
- **Human-in-the-loop.** The workflow must let a human **inspect, correct, and approve** before a
  report is considered final. Show us where and how a person intervenes.
- **Repeatability & adaptability.** This is a **pass/fail requirement, not a preference** (§1.18).
  Running the system again on the same inputs must produce the **same** result, and it must run against
  the **next quarter's** inputs and **reasonable changes in the report's format/structure** without
  rewriting the code. A system that only works for this exact quarter is not a working system.
- **Robustness to imperfect inputs.** Real inputs are messy: labels vary across documents (§1.14),
  evidence may be missing (§1.15), and the inputs folder may contain files that don't belong to this
  client or quarter at all. Handle this gracefully, and make your assumptions explicit rather than
  guessing silently.
- **Verification.** Show how you know the output is correct — the checks and tests you rely on, and
  how you would catch a regression.
- **Usability.** However a human interacts with the system, the experience should be clear and
  appropriate to a high-stakes reporting task.
- **Code quality & architecture.** Clear, maintainable structure with well-reasoned trade-offs.

---

## Part 3 — What to submit

1. **Working code** (any language/stack) with instructions to run it, including how to launch the
   interface described in §1.20 (client + quarter as the only required inputs).
2. **The generated 4Q25 PMR** (PDF and/or Word) for CPERS.
3. **Your tests / verification** — whatever gives you confidence the output is right, including how you
   confirmed two clean-environment runs agree (§1.18).
4. A **1–2 page write-up**. Cover these four **in depth** — they are the ones we cannot read off your
   code:
   - what in your pipeline is **LLM-driven versus deterministic code**, and why you drew the line
     where you did (§1.16);
   - how you **verify correctness**, and how you would catch a regression;
   - **where a human reviews, corrects, and approves** in your workflow, and how your system
     distinguishes a draft-stage warning from a finalization blocker (§1.15);
   - how you would run it for the **next quarter without code changes** (§1.18), and how it handles
     **reasonable changes to the report's format**.

   Then **one or two sentences each** on:
   - your architecture and the key decisions and trade-offs;
   - in what form traceability exists (e.g., a manifest) (§1.17);
   - how you handled **ambiguity, imperfect inputs, and entity resolution across documents** (§1.14–§1.15);
   - what you would improve with more time.

A focused, well-reasoned partial solution with a clear write-up beats an over-engineered one.

**There is no fixed hour budget.** We are evaluating whether you can recognize what *finished* means
for a client-facing report: every figure reconciles to the source, the format matches the prior
quarter, and the process re-runs on new inputs without code changes. Submit when it meets that bar —
and tell us what you deliberately left out, and why.

**Please return your submission within 4 calendar days of receiving this package.**

### How we will run it

So you can build against a known target rather than guess:

| | |
|---|---|
| **OS** | Windows 11. If you develop on macOS or Linux, avoid OS-specific paths and shell calls. |
| **Runtime** | Python 3.12+. If you use another stack, include everything needed to run it. |
| **Dependencies** | Ship a manifest (`requirements.txt`, `pyproject.toml`, or equivalent) that installs cleanly with one command. Pin versions. |
| **Network** | Available. If you use `docling`, note that it downloads models on first run — say so in your README and make sure a cold run still completes. |
| **Docker** | Allowed but not required. If you supply a Dockerfile, also give us a way to run it without Docker. |
| **API keys** | We set `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. See §1.21 for the no-key expectation. |
| **Inputs** | The unseen set is laid out exactly like `inputs/` — same folder structure, same kinds of file. We point your system at that folder and give it client + quarter (§1.20). |
| **Runtime budget** | A single report should finish in **under 15 minutes** on a normal laptop. There is no fixed cost cap, but a run that spends more than a few dollars of API credit is worth a sentence of justification. |
| **Submission** | A zip or a git repo link, either is fine. Include the generated 4Q25 PMR, your tests, and the write-up alongside the code. |

If anything here blocks you, say so in your write-up rather than working around it silently — telling
us what you would have done differently counts in your favour.
