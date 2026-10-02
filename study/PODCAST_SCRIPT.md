# From Messy Documents to an Auditable Financial Report

## Listening Notes

This is a single-narrator podcast script for Abdullah, written for listening rather than reading code on a screen. The audience is a college computer-science major with no assumed finance background. Short chapter breaks make it easy to resume between workouts. Bracketed pauses are optional production cues, not words to read aloud.

Length: approximately 10,600 words, or about 65-80 minutes at a conversational pace. Chapters 1-6 explain the assignment and concepts; 7-17 explain implementation and verification; 18-22 provide the complete file tour, current status, and interview practice.

Implementation snapshot: October 1, 2026. This explains the code that exists now, not a hypothetical finished product. Testing and model selection can change after this recording. This personal study document is outside the submission packager's included folders.

The spoken script starts below. Reference links at the end are optional reading, not narration.

---

## Chapter 1: What Are We Actually Building?

Abdullah, welcome. Today we're going to take your Vectera assignment apart, understand the business problem, and then rebuild the entire system in your head.

You don't need a finance degree for this. You do need to understand how messy documents become reliable software inputs, how we decide when to trust an AI model, and how we demonstrate that a report deserves someone's confidence.

Here's the assignment in one sentence: someone gives our program a client code and a reporting quarter, and the program produces that client's quarterly investment-performance report from a folder of documents.

Not from a perfectly designed database. From spreadsheets, PDFs, a PowerPoint deck, and a committee decision log.

The report is called a Performance Measurement Report, or P-M-R. It explains what the investments are worth, how they performed, which funds helped or hurt, what new investments were approved, what the market outlook says, and whether the portfolio follows the client's rules.

The report must also resemble the previous quarter's report. Same general structure, similar typography, similar visual treatment. This is client-facing work, not just a notebook that prints the right answers.

Most importantly, every important claim must be connected to its evidence. If someone asks, "Where did that number come from?", our system needs an answer more specific than, "The AI said so."

That's the real assignment. It is a document-processing problem, a financial-rules problem, a verification problem, and a product-design problem together.

The interviewer is also going to run the system on an unseen period, potentially for a different client. That means solving this particular quarter is not enough. We need to implement the rules that generate the answer, not memorize the answer.

One important clarification about the email: Vectera's broader work includes training its own models. This assignment does not require us to train a model. We're building an application that uses existing model APIs in a controlled way.

As we go, keep this sentence in your head: code owns the financial answers; AI assists with interpreting evidence; a human approves the result.

[Pause.]

## Chapter 2: Finance for a Computer-Science Major

Let's define the business objects before we discuss the code.

The client in our supplied example is Cascadia Public Employees' Retirement System, abbreviated C-P-E-R-S. It's synthetic, but think of it as an organization investing retirement money.

That organization owns investments in several real-estate funds. Each fund may own many properties. The client doesn't necessarily buy each building directly. It invests in funds whose managers buy and manage those properties.

A portfolio is the collection of those investments.

A fund is one investment vehicle inside that portfolio.

A sleeve is a grouping of funds. In this assignment there are two sleeves: Strategic and Tactical. The report calls the second commentary section "Tactical and Special Situations," but that doesn't mean there are three sleeves. The data still has two.

Now, net asset value. Usually abbreviated N-A-V. For this assignment, think of NAV as what the investment is currently worth. If a fund has a NAV of fifty million dollars, that is its reported value, not necessarily the amount the client originally put into it.

A commitment is an agreement or authorization to invest money. An approved commitment doesn't necessarily mean the money has been paid yet.

That distinction matters. You can have an investment the committee approved that has no current NAV and no performance return because it hasn't closed or funded.

Now performance.

Income is money the investment earns. Appreciation is an increase in the value of the investment. Appreciation can also be negative, meaning a loss in value. Manager fees reduce what the investor keeps.

The spec gives us a formula for a fund's dollar contribution to quarterly performance: income plus appreciation minus manager fees.

Capital contributions are different. The word "contribution" is slightly overloaded here. A capital contribution means the investor put more money into the fund. A contribution to performance means the fund created or lost investment value.

Suppose you had a fund worth ten million dollars. You deposited another two million. Its ending value is now twelve million, with no investment gain. Your balance rose, but the fund didn't earn a twenty-percent investment return. You added money.

That's why we separate capital flows from performance.

Time-weighted return, or T-W-R, is a return measure designed to remove the effect of the timing of money entering or leaving. It helps answer how the investments themselves performed.

Internal rate of return, or I-R-R, incorporates cash-flow timing. It is useful for a longer-term investment track record.

You may have studied numerical methods for finding an IRR. We do not need to implement one here. The workbook already supplies TWR and IRR. Our job is to read the specified series correctly, not create a more complicated calculation that the assignment doesn't ask for.

The same is true of leverage. Loan-to-value, or L-T-V, measures debt relative to property value. More debt generally means more leverage. The workbook already gives us the correct weighted sleeve figures.

A benchmark is a comparison series. It helps answer whether this client's investments performed better than the designated reference. The client's custom benchmark is not interchangeable with every market index mentioned in the PowerPoint deck.

A basis point is one hundredth of a percentage point. If one return is five percent and another is four percent, the difference is one percentage point, or one hundred basis points.

Finally, the deck may discuss net operating income, N-O-I, and capitalization rates, or cap rates. NOI is property income after operating costs, before financing and capital spending. A cap rate relates that income to property value. Holding income constant, a lower cap rate implies a higher property value. Don't describe cap-rate compression as falling property values. That reverses the relationship.

You don't need to become an investment analyst. You need to understand these distinctions well enough to defend why our code reads one column instead of another.

[Pause.]

## Chapter 3: Reading the Spec Like an Engineer

The spec has three parts: the domain rules, the evaluation criteria, and the submission requirements.

Part One tells us what to implement. Part Two tells us what matters most. Part Three tells us what to deliver and what environment it needs to run in.

Let's walk through all the numbered requirements, grouping related ones so this sounds like a story rather than a legal reading.

Section one point zero is the glossary we just covered. Notice its important instruction: read the provided TWR and IRR. Don't recompute them from cash flows. The prior report mentions Modified Dietz in its disclosure. We preserve the disclosure; we aren't being asked to implement that methodology.

Section one point one gives the report structure. The output needs portfolio overview and guidelines, fund statistics, managers, an annualized return chart, performance commentary, commentary for both sleeves, recent activity, market update, allocation history, diversification, compliance, disclosures, and the flash appendix.

Section one point two defines the sleeves and the benchmark labels. Those labels have financial meaning, so we preserve the relevant distinctions.

Sections one point three through one point five define attribution. Calculate dollar contribution. Select the two largest positive contributors, the two largest negative detractors, and the two largest positions by ending market value. Don't rank by percentage return. Don't introduce an arbitrary million-dollar threshold. Don't select a fund merely because its manager report exists.

The lists can overlap. One fund can be a large position and a detractor. Write it up once, and state both roles. The spec also says the broader sleeve commentary is not restricted to those ranked funds.

There is an edge case when fewer than two funds have a negative contribution. Feature the negative ones that exist and explain the rest. Our current wording distinguishes positive and zero contributions, rather than pretending a zero contribution is positive.

Sections one point six and one point seven concern new commitments. Approvals that haven't funded belong in recent activity, not in performance commentary. We describe their strategy using their one-pagers, lead with the largest new commitment, and don't invent returns for them.

Open approvals also count in committed-or-approved capital and investment-position counts. We must consider approvals before quarter-end, including earlier years, then remove those that were withdrawn or lapsed. The committee log is firm-wide, so filter by client, category, date, and decision outcome. It is unsorted, so row order is not chronology.

Section one point eight is reconciliation. Individual funds must add up to their sleeves. Sleeves must add up to the portfolio. Every figure must tie to the authoritative source.

Section one point nine defines compliance. Read sector concentration from the property sheet. Read weighted leverage from sleeve subtotal rows. Read fund-level foreign exposure from Funding Status, not the look-through geography sheet. Compare the designated one-year net return with the designated one-year benchmark return.

Section one point ten says the market update must condense the house-view deck and reflect its charts. The difficulty is that these charts are pictures. Their data isn't available as editable chart cells. Also, broad market indices in the deck are not the same series as the client's custom benchmark.

Section one point eleven requires the current flash PDF in the appendix. Section one point twelve makes the previous report both a format example and a comparison baseline.

Section one point thirteen forbids manually transcribed material facts. A person can't read a chart and type all its values into a configuration file so the program appears to extract them. Software extracts first; a human can then inspect and correct that extraction.

Section one point fourteen requires controlled, traceable, conservative entity resolution. Similar labels must be matched by explicit rules, not an opaque model guess. Ambiguous matches need attention.

Section one point fifteen explains missing evidence. Missing supporting commentary can be a warning. Missing information necessary for a required result must block finalization. Neither permits inventing facts.

Section one point sixteen draws the AI boundary. Models can help read images and select or synthesize text. Math, ranking, filtering, reconciliation, and compliance must be deterministic. Textual claims need verification against their source. Image values need source locators and human confirmation.

Section one point seventeen requires machine-readable traceability. Not just footnotes in a PDF. We need structured records naming the file and specific cell, page, or slide.

Section one point eighteen is reproducibility and adaptability. The same inputs must give the same meaningful results. Prose can vary, but figures, fund choices, ordering, roles, compliance, and structure cannot. Client-specific limits must come from inputs. Rows and fund counts can change. Hardcoded quarter-specific answers are a rejection, not a minor deduction.

Section one point nineteen requires visual fidelity. Correct math in an unrelated-looking report isn't enough.

Section one point twenty defines the user interface contract: client code and quarter are the only required report inputs. The program finds the files.

Section one point twenty-one restricts tools. PDF reading must use Docling, PyMuPDF, or pdfplumber. Models must be accessed through OpenAI or Anthropic. Keys come from the environment. If keys are missing, still produce a complete deterministic financial draft; mark model-dependent omissions clearly.

Part Two prioritizes correctness, faithfulness, auditability, human supervision, repeatability, robustness, verification, usability, and code quality.

Part Three requires code and run instructions, the generated report, tests or verification, and a one-to-two-page write-up. That write-up must explain the AI boundary, correctness checks, review workflow, and next-quarter behavior, plus trade-offs and limitations.

The target is Windows Eleven with Python three point twelve or newer. Dependencies must be pinned and installable with one command. A report should finish within fifteen minutes on a normal laptop. Docker is allowed, but a non-Docker path is still required. A ZIP or repository link is acceptable.

The email adds the live unseen-input walkthrough and permits coding AI. The lesson is not "avoid AI." It's "show judgment about where AI belongs."

[Pause.]

## Chapter 4: What's in the Input Folder?

Let's build a mental map of the actual files.

The current-quarter flash workbook is called flash, four-Q-twenty-five, dot x-l-s-x. It is our principal numerical source.

Funding Status gives investment composition, commitments, funding, market values, and designated portfolio summary returns.

Cash Activity gives beginning value, capital flows, income, fees, appreciation, ending value, and leverage.

Returns and Multiples gives fund returns, IRRs, and equity multiples. Annual Returns gives the annualized chart series and designated benchmark return. All Property and All Geographic give diversification percentages.

There is also a PDF rendering of that current flash. We append the supplied PDF rather than trying to reproduce every spreadsheet page ourselves. The workbook owns calculations; the supplied PDF owns the appendix presentation.

The previous-quarter PMR is the third-quarter twenty-twenty-five PDF. It supplies layout clues, policy limits, static mandate information, disclosure language, and comparison facts.

There is an older second-quarter PMR too. That tests whether we identify the most recent relevant prior report instead of opening whichever filename we see first.

There is a third-quarter flash workbook and a fourth-quarter workbook for a different client. These are distractions by design. We must ignore them for this run.

The investment committee workbook covers twenty-twenty-five. It includes different clients, different types of decisions, and different outcomes. We can't simply sum every line that mentions a commitment.

Allocation History supplies the historical target-allocation and NAV series for the allocation-over-time exhibit.

The Market Outlook PowerPoint supplies narrative text and seven chart images. The file has thirteen slides. The difficult facts live inside the image pixels, not just in slide text.

Finally, the manager-report folder has seven PDFs. They cover Cornerstone, Redwood, Ironwood, Kestrel, Tidewater, Northgate, and Ridgeline. Some provide current performance commentary. Others provide strategy descriptions for new approvals.

Northgate and Ridgeline are especially important for recent activity. Tidewater's wind-down information is useful context. Ironwood demonstrates naming variation: a Roman numeral in one place, an Arabic numeral and legal suffix in another.

One major detractor, Meridian, has no current manager PDF. That's a deliberate test of whether we retain a financially important fund even when supporting narrative is missing.

Think of the inputs as a collection of typed evidence sources. Each has a job. They aren't interchangeable documents that we dump into one giant prompt.

[Pause.]

## Chapter 5: The Architecture in One Pass

Imagine the user has started our application and entered a client and quarter.

First, we parse the reporting period and locate the correct documents by their contents.

Second, we read the workbook into structured financial objects. We calculate contributions, rankings, portfolio composition, and compliance. We also run reconciliation checks.

Third, we process committee events to determine new approvals, current open approvals, and relevant reversals.

Fourth, we gather supporting manager passages and extract market-deck text and images. An available AI model can select exact quotations and read labelled chart values.

Fifth, we build a shared report model. Think of this as an intermediate representation in a compiler. Instead of source code becoming machine instructions, financial evidence becomes ordered report sections containing paragraphs, tables, charts, and evidence references.

Sixth, that model feeds two outputs: a PDF for reading and an HTML page for inspection and approval.

Seventh, a reviewer checks the evidence and chart readings. The system refuses finalization if a blocker remains or source inputs changed after generation.

That is a staged pipeline. Each module has a relatively clear ownership boundary.

We are not using a free-roaming model agent that decides which tools to call until it feels finished. The assignment calls the system an agent, but our implementation is better described as an evidence-grounded workflow with bounded model assistance.

Why? Because the required process is known. Explicit stages make failure behavior, auditability, and repeatability easier to reason about.

The main orchestration file is pipeline dot p-y. It coordinates these stages, writes output artifacts, records input hashes, and produces the verification summary.

Its job is coordination, not to hide every business rule in one giant function. The financial rules live elsewhere. The rendering rules live elsewhere. The provider details live elsewhere.

That separation means a change to PDF styling shouldn't change fund rankings. Changing model providers shouldn't change the cash-flow formula. Those are useful boundaries to explain in an interview.

[Pause.]

## Chapter 6: Is This RAG?

You've probably heard the phrase retrieval-augmented generation, usually pronounced rag.

Here's the background. A model's training doesn't automatically contain your private documents. Even if it did, you wouldn't want it guessing this quarter's numbers from memory.

Retrieval-augmented generation supplies relevant external evidence when the model answers. In a conventional setup, documents are split into chunks. An embedding model converts each chunk into a vector. A query is also converted into a vector. Search finds nearby vectors, retrieves the associated passages, and adds them to the model's context.

Semantic similarity is useful when people ask open-ended questions across large collections. But a nearby vector isn't proof that a passage is the correct authoritative source. It can retrieve a plausible passage from the wrong quarter, miss a crucial row, or lose context when a table is split into chunks.

Our system follows the grounding principle, but it does not implement a conventional embedding-and-vector-database RAG stack.

We have no vector database, no embedding index, and no LangChain dependency. We locate evidence using document identity, workbook labels, report headings, quarter dates, and explicit entity rules. The model receives the relevant passage or chart image directly.

Call it structured retrieval with grounded extraction. Or simply an evidence-grounded document pipeline. Don't tell the interviewer we built a vector-search system when we didn't.

Why not add one? The sources are small enough and their contracts specific enough that deterministic retrieval is a better fit for the core financial facts. We know the sheet and column meanings we need. Fuzzy search shouldn't choose which return series controls compliance.

RAG also doesn't automatically solve hallucination. Supplying evidence doesn't ensure the model uses it correctly. You still need to validate the answer.

We take an especially conservative approach with text. Instead of asking the model to freely paraphrase an explanation, we ask it to select exact sentences from an extracted passage. Code verifies that each accepted quotation occurs in the source text.

That creates a narrower, more defensible contract. The model can choose among available source sentences. It cannot successfully introduce a sentence about a property purchase that doesn't exist in that passage.

There are still limitations. An exact quotation can be irrelevant, misleading without context, or based on a poorly extracted passage. Substring verification establishes source presence, not a complete semantic proof. That's why review still matters.

If the document collection became much larger, retrieval could evolve. We'd likely combine exact client-and-period filtering with semantic retrieval for commentary. We would still keep financial computation outside the model.

[Pause.]

## Chapter 7: Ingestion, Discovery, and Entity Resolution

Now let's go inside ingest dot p-y.

Ingestion means converting external documents into values our code can work with. Discovery means deciding which documents belong to this report before we extract their facts.

We use openpyxl for Excel. It lets Python read workbooks, sheets, rows, and cells without launching Microsoft Excel.

We load with data-only enabled. For formula cells, that reads the value last cached by the spreadsheet application. It does not run Excel's calculation engine. This is important: if someone supplies a workbook with missing formula caches, our parser cannot magically calculate all Excel formulas. We should detect missing required numeric values rather than pretend they exist.

For candidate flashes, discovery looks for the expected Funding Status sheet, relevant period text, and the client code in benchmark labels. It doesn't trust the filename as the sole authority.

Once the current flash is identified, we read the client's full name from the workbook. We don't maintain a source-code dictionary that maps only CPERS to its full name.

For PDFs, PyMuPDF extracts page text. We identify prior client reports by content, choose the latest available period before the requested period, and retain page numbers for evidence.

Why PyMuPDF? It's an approved parser. It can extract text, inspect font information, render pages for inspection, and append PDF pages. That gives us several capabilities without an office installation or a separate document-processing service.

There are trade-offs. PDF text is often positioned visually rather than stored in natural reading order. A scanned document may contain an image instead of extractable text. Our current implementation targets the supplied text-based PDFs; it doesn't contain a general scanned-document OCR pipeline.

Within spreadsheets, we search for labels and headers instead of fixed cell addresses. If four rows are inserted above a table, its header can still be found. A header map turns column names into indices.

Some return tables have grouped headers. A top row says "One Year," while the next row says "Net" and "Gross." We combine those layers so code can request "One Year Net" rather than guess the third column.

Normalization matters here. We normalize punctuation and case, but preserve the distinction between dollar and percentage headers. If both dollar and percentage symbols were simply deleted, "Market Value in dollars" and "Market Value in percent" could collapse into the same lookup key.

The Sheet helper records cell locators when it reads facts. A source coordinate like B-twenty-three is output provenance, not a hardcoded instruction to always read B-twenty-three. We discover the location first, then record it.

Now entities. We normalize some punctuation, trailing legal suffixes, U-S punctuation, and Roman numerals. That lets Ironwood Fund Three and Ironwood Fund I-I-I resolve together under an inspectable rule.

But Fund Four and Fund Five remain different. We don't strip every distinguishing token or accept whichever fuzzy match scores highest.

Manager-document matching requires a normalized complete source line matching the expected entity. Accepted and rejected decisions are recorded. Multiple possible matches trigger a blocker rather than a model deciding silently.

The matching rules aren't universal. Some cross-sheet lookups use normalized exact labels rather than a complete alias system. Client identification and policy extraction also rely on the stated document contract. Arbitrarily different labels or layouts may need a new adapter.

That is the honest scope: resilient to specified and tested changes, not a universal parser for any finance document ever created.

[Pause.]

## Chapter 8: The Financial Engine

Finance dot p-y is where the deterministic business rules live.

Let's return to attribution. For each fund we read income, appreciation, and manager fees. We add income and appreciation, then subtract fees. That's the contribution to investment performance.

Suppose Fund A adds fifty thousand dollars on a one-million-dollar position. Fund B adds two hundred thousand dollars on a twenty-million-dollar position. Fund A has the higher percentage gain, but Fund B contributes more dollars to the portfolio. The spec wants Fund B ranked ahead by contribution.

We create three ranked lists: positive contributors, negative detractors, and largest NAV positions. We take up to two from each list and attach every applicable role to each fund.

For ties, we use a normalized alphabetical name as a deterministic tie-breaker. That prevents incidental row order from changing role selection when values are equal.

The current results illustrate why overlapping roles matter. Redwood is the largest contributor and second-largest individual position. Ironwood is the second-largest contributor. Meridian is the largest detractor. Cornerstone is the second-largest detractor and largest individual position.

Four distinct funds fill six role slots. The application derives that from source data. Those names aren't rules in the production pipeline. They are valid golden expectations in the tests for this supplied dataset.

Next, cash roll-forward. Beginning market value, plus investor contributions, minus distributions and withdrawals, plus income, minus fees, plus appreciation, should equal ending market value.

The capital flows belong here even though they don't belong in attribution. Different formulas answer different questions using some of the same columns.

We also compare ending cash-sheet values to funding-sheet NAV, sum funds to sleeve totals, sum sleeves to portfolio totals, check commitments, and check diversification totals.

The ledger records actual value, expected value, difference, tolerance, and pass or fail. We do not repair a discrepancy by replacing the source value with whatever makes the equation work.

Our money reconciliation tolerance is two cents, to accommodate displayed source rounding. The exact differences remain visible. Percentage diversification checks also have their own numerical tolerance; those are percentage points, not cents.

There is an implementation detail worth knowing: the calculation layer currently uses Python floating-point numbers read from the workbook. Display formatting for money uses Decimal with half-up rounding. That doesn't mean every financial operation is already Decimal-based. A more rigorous production ledger could use Decimal or integer cents end-to-end for monetary arithmetic.

Now compliance. Client-specific policy limits come from the prior report. They are not constants copied from this quarter into the business logic.

Sector concentration is the largest property-type percentage, and we name the sector. Leverage uses the provided weighted Strategic and Tactical subtotal values. We don't average fund ratios.

Why not average ratios? Suppose one fund has a tiny asset base and another has a huge one. Giving their percentages equal weight would misrepresent the portfolio. More generally, the correct weight for a financial ratio depends on its denominator. The spec already identifies the authoritative weighted value, so we read it.

Foreign exposure has two legitimate measures. One classifies funds themselves as U-S or non-U-S. Another looks through funds to the location of underlying properties. A U-S fund can own foreign property. Those percentages can differ without either being wrong.

Compliance uses the first measure. The geography exhibit uses the second. We explain the distinction in the report.

The return objective compares the portfolio's specified one-year net TWR from Funding Status with the benchmark's specified one-year net return from Annual Returns. We don't select a nearby series because its label looks familiar.

The annualized chart reads its horizons from the prior report, then reads the relevant supplied return columns. We don't calculate an IRR, rederive TWR, or average fund returns into a homemade total.

The central idea is source authority: each financial fact has a defined owner. Correct engineering means honoring that owner even when another worksheet or market slide shows a related but different number.

[Pause.]

## Chapter 9: Committee Decisions as an Event Stream

The investment committee log is one of the most interesting parts of this assignment.

Think of it as a stream of events affecting investment state.

An approval opens a commitment. A withdrawal or lapse removes it from the open set. A deferral doesn't open a commitment. A future event should not affect a historical quarter-end report.

This is similar to event-sourced reasoning, although we haven't built a complete event-sourcing platform. We take the available log, sort relevant events chronologically, and reduce them into a quarter-end state.

Filtering is mandatory. We require the requested client, Commitment category, an event before the quarter-end boundary, and a recognized committee action. The boundary is the first day of the next quarter, so "before that date" includes the entire reporting quarter.

We distinguish three outputs.

New approvals are approved events during this quarter. They belong in recent activity.

Open approvals are still live at quarter-end, even if they began earlier. We exclude investments already carried as funded holdings. They affect committed-or-approved capital and position counts.

Reversals are relevant withdrawals or lapses during the quarter for approvals mentioned previously. They get an explanatory activity note rather than quietly disappearing.

The supplied data gives us Northgate and Ridgeline as current open approvals, totaling sixty-five million dollars. Northgate is larger, so it leads recent activity. The earlier Alder Creek and Sentinel approvals were withdrawn or lapsed and must not remain in open totals.

We parse the explicit U-S-D amount and its million-or-billion unit from log text using regular expressions. That's deterministic extraction of stated text, not an AI calculation.

A regular expression is a formal pattern matcher. It works well when the expected syntax is constrained. It's not a general language-understanding system. If a required amount doesn't match, we flag a blocker rather than invent a number.

If the action is something unrecognized, such as "maybe approved," we exclude that event from totals and flag it. The spec explicitly tells us not to guess.

One limitation to acknowledge: complex repeat approvals, identical-day contradictory decisions, or substantially different reversal naming could require a richer event identifier and conflict policy. Our current chronological reducer is suitable for the supplied contract, but those are good extension points.

The lesson is that current state isn't the sum of all historical approval rows. It is the result of interpreting a sequence of decisions with time boundaries.

[Pause.]

## Chapter 10: The Evidence Ledger

Evidence dot p-y gives the pipeline a shared ledger.

The ledger stores facts, issues, entity-matching decisions, and verification checks.

A direct fact records a value and a source locator. For a spreadsheet value, the locator includes file, sheet, and cell. For a PDF passage, file and page. For a chart image, file, slide, chart, and the retained image asset.

A derived fact also records a formula and the identifiers of its input facts.

That produces a small provenance graph. Nodes are facts. Edges connect a calculation to its inputs. Click a contribution in review, and you can follow it to income, appreciation, and fees. Then follow those to workbook cells.

It is analogous to a compiler dependency graph or a spreadsheet formula graph, but designed for auditability.

We create stable fact identifiers from a hash of the fact record. A hash turns input bytes into a fixed-length digest. The same serialized content produces the same digest. Change the content, and the digest will overwhelmingly likely change.

We use S-H-A-two-fifty-six through Python's hashlib. JSON keys are sorted for consistent serialization where the digest helper is used. Fact identifiers use a shortened prefix; full hashes are used for important document integrity records.

A hash is not encryption. It doesn't hide a sensitive fact. It is also not a signature proving who approved something. It is a content fingerprint.

That distinction is important because we use hashes in several places: evidence identifiers, model-response cache keys, draft-integrity checks, source-file checks, and reproducibility comparisons. Similar mechanism, different purpose.

The review UI attaches evidence references at report-block level. A table can point to several relevant facts, and a paragraph can point to its source values. This is much stronger than a page-wide generic citation, but it isn't yet a perfect cell-by-cell or phrase-by-phrase citation interface.

The output file evidence dot JSON exposes this ledger for a human or another program. JSON is useful because it preserves structured fields rather than forcing someone to scrape source descriptions from prose.

Traceability doesn't make an incorrect formula correct. It makes the formula and its evidence inspectable. That's why we need both provenance and verification.

[Pause.]

## Chapter 11: What the Model Actually Does

Models dot p-y is the provider boundary.

Our application can use OpenAI or Anthropic. If both keys are present, it chooses OpenAI. If only Anthropic is present, it chooses Anthropic. If neither is present, it skips model calls and continues with a source-only draft.

The current OpenAI default is a pinned GPT-four-point-one-mini snapshot. The Anthropic default is Claude Sonnet four point six. An environment setting can override the model identifier. A different model still has to support the request format our adapter sends; we don't claim every model is automatically interchangeable.

The code sends H-T-T-P requests using Python's standard-library urllib rather than adding a provider SDK. That's a small-dependency trade-off. It is simple for the two request shapes we need, but an SDK could provide better convenience, retry handling, and typed responses in a larger application.

We set temperature to zero, request a JSON object, limit output tokens, use a per-request timeout, and enforce an overall model-time budget.

Temperature relates to token selection. Lower temperature tends to favor the highest-probability continuations. It is not a mathematical guarantee that independent hosted API requests will be identical.

Also, JSON-object output is not the same thing as strict schema enforcement. It asks for machine-readable JSON. Our code still has to validate that expected fields and numeric values are present.

The text task is exact quotation selection. The model chooses up to three useful source sentences. Code keeps only strings that occur in the supplied passage. If model access fails or no valid quotes survive, we use deterministic heading-delimited source extraction instead.

The image task reads labelled chart values. We supply the chart image and ask for a title, series labels, values, units, useful highlight indices, and uncertainties. We explicitly ask it not to estimate unlabelled points or confuse axis ticks with data labels.

Why vision? A PowerPoint picture does not contain an accessible table of bar values. Reading slide text alone would miss the evidence the spec deliberately put in pixels.

The returned series must be nonempty and contain finite numeric values. Infinity and not-a-number are rejected. But current validation is basic. It doesn't yet fully check units, label completeness, axis bounds, or every cross-chart relationship.

For example, a well-formed JSON object containing a plausible but wrong percentage is still wrong. Syntactic validation is not semantic validation.

Every accepted image extraction carries its original image and slide locator and requires human confirmation. We extract all seven images, although the current concise market section presents highlights from the first three available charts. All extracted charts remain available for review. A more deliberate portfolio-relevance selection across the complete deck is a potential improvement.

Narrative dot p-y handles the supporting passages, slide text, image extraction, and allocation-history parsing.

A PowerPoint file is internally a ZIP archive of XML and media. We use zipfile and an XML parser to follow slide relationships to the embedded images. We don't need to run PowerPoint or use an office automation service.

We retain slide order and image locators. We select house-view text from recognized themes, risks, and positioning slides, rather than copying the entire presentation.

The image prompt says to treat image contents as data, not instructions. That's a small prompt-injection precaution. The larger safety measure is restricting the model's role: it doesn't have shell tools, doesn't choose financial rules, and doesn't directly approve anything. We haven't implemented a complete adversarial-document security framework.

On failure, diagnostics avoid printing API keys or request headers. A timeout or malformed response reduces enrichment and creates an issue; it doesn't destroy the financial draft.

Missing model access blocks final approval of required image data, but not generation of the deterministic report. That is exactly the difference between graceful degradation and silently pretending everything is complete.

[Pause.]

## Chapter 12: Caching, Credentials, and Cost

Caching means saving a result so identical future work doesn't have to be repeated.

Our model cache key depends on provider, model identifier, prompt, and image content. If any changes, it gets a different key. The API key itself is not part of the cache key and is never written into the response cache.

This is application-level response caching, not merely a provider discount for repeated prompt prefixes. On a successful cache hit, the application reuses the saved JSON without calling the model.

That helps speed, cost, and repeatability on repeated runs. But there is a catch: a cached wrong answer remains wrong. Caching is not correctness verification. And a warm-cache repeatability test can hide variation that appears on independent fresh API calls.

That's why our repeatability script uses separate empty output folders and caches.

Credentials are loaded by config dot p-y using python-dotenv. The local dot-env file lets you paste a development key without typing it into each terminal. Existing environment variables take precedence, so the evaluator's keys aren't overwritten by a local file.

Only one provider key is required. Anthropic is optional when you're using OpenAI. The dot-env-example file is a safe blank template. The actual dot-env is excluded from source sharing and the submission ZIP.

There is also a setting to disable dot-env loading during offline verification. Otherwise a supposedly no-key test could accidentally pick up your local key and make live calls.

No key should mean an explicitly incomplete enrichment path, not a startup crash.

About cost: we have not measured a live run yet. Earlier estimates were rough planning estimates for a small number of quotation and image requests, not observed bills. The verification output records call counts and provider token usage to support measurement once we run it live.

A larger model may improve chart-reading accuracy, but we should benchmark it against known chart labels. A more expensive name is not evidence. The model should be chosen on actual extraction quality, response compatibility, latency, and cost.

The current timeout controls are guardrails, not proof that the complete system meets the fifteen-minute budget on the evaluator's laptop. Dependency setup, document parsing, rendering, and network behavior still need real timing.

[Pause.]

## Chapter 13: Turning Evidence into a PDF

Report dot p-y constructs the report sections, generates charts, and renders the PDF.

The shared report model is important. Both the PDF and the review page come from the same section data. We avoid having one set of calculations for the PDF and a different set for the UI.

The model contains paragraphs, tables, and chart references. Each block carries evidence identifiers. Financial connecting prose is generated from source-backed values, not freely invented by a model.

Matplotlib produces charts from structured workbook data. We use its noninteractive backend, called Agg, so charts render without opening desktop windows. That works well for a command-line reporting application.

We generate annualized returns, allocation history, property diversification, and geographic diversification. These workbook-driven charts are separate from the house-view chart images we're asking the model to read.

ReportLab creates the PDF. Its flowing layout system lets paragraphs, tables, and images occupy pages, with deliberate page breaks for important groups. Table headers can repeat across pages. Text is escaped so source characters don't accidentally become formatting instructions.

PyMuPDF then appends the supplied flash PDF. We preserve its six pages rather than recreating it or compressing every appendix page to force the overall report into the example's page count.

The current no-key draft is seventeen pages, compared with thirteen in the previous report. That difference is documented. It doesn't mean layout fidelity is finished just because the sections exist. We need readable tables, consistent styling, and final visual inspection.

Template dot p-y extracts reusable style information from the prior PDF: common body font and size, primary color, heading size, and recognized contents order.

One bug we caught is a useful example. Lots of small table cells can dominate a naive font-frequency count. White header text can also be selected as an apparent important color. That would produce unreadable style choices. We changed the extraction to weight body text by length and exclude inappropriate color candidates.

The current body size is about nine point two points, and the main heading size is fifteen. The system uses portable built-in PDF fonts and flags unsupported template fonts for substitution.

However, this is not full automatic reconstruction of every visual detail. Some table styling, secondary colors, page grouping, and layout dimensions are still explicitly implemented. If the prior report changes completely, we don't promise an identical redesign with zero engineering work.

We can recognize and reuse supported section order. An unfamiliar structure generates a review issue rather than magically gaining a new financial implementation.

The renderer also distinguishes draft from approved. The draft has visible draft labeling. Only the approval path renders the approved report.

Presentation is part of correctness in a client-facing workflow. A table with clipped labels or a chart whose series is unreadable can communicate the wrong thing even when the underlying values are right.

[Pause.]

## Chapter 14: Human Review Is a Real Workflow

Review dot p-y creates the HTML evidence-review page and handles approval through a local server.

The page shows report content alongside verification results, issues, evidence, chart images, and approval controls. Selecting a report block opens its facts and recursively follows calculation inputs.

You can inspect an automatically extracted chart beside its image, edit its extraction JSON if necessary, and confirm the values.

This isn't a polished spreadsheet-like chart editor yet. Editing JSON is a practical prototype trade-off. It exposes structured data clearly but isn't the most ergonomic interface for every analyst.

Financial values can't be arbitrarily changed in the browser. If the authoritative workbook is wrong, correct the workbook and regenerate. That creates a new reviewable draft rather than an undocumented overlay that silently changes the report.

For chart images, the rules allow correcting the software's existing extraction. They don't allow a human to replace a completely absent automatic extraction by typing every value manually. So if initial image extraction failed, rerun with working model access before finalization.

We distinguish warning, blocker, and review-needed issues.

Meridian's missing manager commentary is a warning. We can still show its financial contribution and role because the flash has those values. We don't invent property-level reasons for its decline.

A reconciliation failure is a blocker. Missing required policy is a blocker. Missing required chart extraction is a blocker. Available chart extractions require confirmation.

Before approval, the browser asks for a reviewer name and acknowledgment. The backend separately checks a reviewer name, the expected draft hash, current source-file hashes, blocker status, and confirmation of every chart.

The hash checks address a time-of-check versus time-of-use problem. Suppose you reviewed a draft, then someone changed the workbook. The old approval shouldn't apply to the new input. We compare the source content at approval time with the hashes recorded at generation time.

Similarly, if draft JSON changes outside the controlled workflow, its stored fingerprint no longer matches. The application refuses approval and asks for regeneration.

After successful approval, we rebuild sections from reviewed data and render final-report dot PDF. We write approval dot JSON with reviewer, time, confirmations, corrections, and a hash of the final PDF. We also save final evidence and final sections.

This is local workflow integrity, not enterprise authentication. Someone with write access to all local files could tamper with files and recompute hashes. A typed name isn't a cryptographic identity. The server has no multi-user login or role-based authorization. Browser acknowledgment is not a strong backend-enforced identity control.

We bind to loopback, the local computer, instead of exposing the server to the network by default. For a hosted system, we'd need authentication, authorization, stronger storage controls, more complete request protection, and a durable audit trail.

The important accomplishment is that review isn't a decorative button. It is a state transition from draft to approved with explicit preconditions and recorded evidence.

[Pause.]

## Chapter 15: What Reproducibility Really Means

There are several different claims people confuse under the word reproducibility.

Environment reproducibility means compatible software dependencies are installed. Pinned versions and an isolated Python environment help with that.

Computational reproducibility means the same source data produces the same calculations, rankings, and statuses. Deterministic code and explicit tie-breakers help with that.

Model-output reproducibility concerns independent API calls. Temperature zero and a fixed snapshot can reduce variation, but they don't prove every extracted image value is stable.

Byte reproducibility concerns identical files. A PDF timestamp or serialization detail can change bytes even when the report means the same thing. The spec is primarily concerned with meaningful answers, not necessarily identical PDF bytes.

Our pipeline writes a financial hash covering portfolio data, funds, sleeves, activity, policy, compliance, history, diversification, and section order. It also writes a broader report-model hash.

The repeatability script runs the CLI twice in separate Python processes with separate temporary output directories and fresh model caches. By default it removes keys and disables local dot-env loading.

Those are fresh processes and output directories within the installed environment. They are not two independently provisioned clean Windows machines. That's a narrower claim, and it's the correct one.

The current script passes or fails based on equality of the financial hashes. It separately records equality of the full report-model hashes.

Here's a critical remaining gap: the financial hash excludes model-extracted market chart data. So a passing financial comparison does not establish that every chart number is repeatable across fresh live calls.

The spec requires every meaningful figure to agree, including chart figures. We still need to compare those independently on uncached live runs and make that result part of the actual acceptance check.

Nor is identical output necessarily correct. Two runs can make the same wrong calculation. Reproducibility is one property; fidelity to source evidence is another.

Docker could package the runtime environment, but it wouldn't freeze an external model service's behavior or prove the chart extraction correct. Terraform provisions infrastructure. It doesn't make our local financial pipeline deterministic.

Neither tool is currently part of this project. That's an implementation fact, not a statement that these tools are bad. They solve different problems.

Our next verification should distinguish all these layers: clean installation, deterministic finance, fresh image extraction, human confirmation, and performance on the evaluator's target environment.

[Pause.]

## Chapter 16: Tests That Try to Break Our Assumptions

We use pytest for automated tests. There are currently twenty-three passing tests in the latest full local run.

Let's explain what those tests mean rather than just advertising the count.

Test Finance contains golden expectations for this supplied quarter: the portfolio NAV, selected return and exposure values, role assignments, open approval totals, and reversals.

A golden test checks known-good answers for a known fixture. That's allowed and desirable. Hardcoding those answers into the production pipeline would be different and would fail the spec.

We also mutate the inputs.

One test inserts rows and renames the current flash. If the code secretly relies on a fixed row or filename, that should break it.

Another reverses committee-log row order. The answer should remain the same because dates, not row positions, determine chronology.

Another adds a zero-balance fund. Fund count changes, but financial totals still foot and it shouldn't suddenly gain a top role.

Another changes client identity, benchmark label, and policy values in a synthetic fixture. The financial layer must read the new information instead of repeating CPERS constants. That is useful evidence, but not a full end-to-end test on a real unseen client package.

We deliberately corrupt a cash value to ensure reconciliation creates a blocker. We insert an unknown committee action to verify conservative handling. We add a post-quarter approval to confirm it doesn't leak into historical activity.

Test Pipeline exercises complete no-key draft generation, report text and structure, repeatability, refusal to approve missing chart values, external draft tampering, and a mocked chart-correction-to-finalization path.

Mocking means replacing a dependency with a controlled fake during the test. We can simulate a successful chart response without network access and test the downstream review logic.

A mocked chart test proves that the approval pipeline handles a supplied extraction. It does not prove a real model can read the actual chart accurately. Never blur those claims in the walkthrough.

Test Models rejects invented quotations, checks that API failures preserve a safe draft without leaking a secret, and verifies that a second identical request uses the application cache.

Test Template prevents the unreadable-font-and-color regression we discussed earlier.

Test Config checks that local credentials load literally, external environment keys win, and offline verification doesn't accidentally load a private key.

Test Launcher checks dependency-install reuse, reinstall after a requirements change, no completion marker after a failed install, and the client-and-quarter prompt-to-review handoff.

These are selected risk-focused tests, not a proof of universal correctness. We still need actual Windows execution, live-provider image evaluation, broader layout fixtures, source-mutation coverage, and more schema edge cases.

There's a GitHub Actions workflow for Windows and macOS with Python three point twelve. It installs dependencies, runs tests, and runs the repeatability script. The existence of the workflow is not an observed passing run. Until it runs on a hosted runner, Windows remains unverified.

The best testing story is specific: "Here is the assumption. Here is the test that challenges it. Here is the failure we expect to detect."

[Pause.]

## Chapter 17: The One-Command User Experience

You pushed for ease of use, and that was a good product requirement.

The Windows entry point is start dot c-m-d. Run it, enter the client and quarter, and the program handles setup, generation, and opening review.

The command file switches to its own directory, so running it from a different working folder doesn't make relative input paths point somewhere random. It invokes Python three point twelve through the Windows Python launcher and forwards optional arguments.

Scripts slash launch dot p-y is the bootstrap program. It uses the standard library so it can run before project dependencies exist.

It creates a dedicated virtual environment named dot-launcher-venv. A virtual environment isolates this project's installed Python packages from your global installation and other projects.

Then it hashes requirements dot t-x-t and checks a completion marker. On first use, or when the manifest changes, it installs the pinned dependencies. It writes the marker only after installation succeeds. Later launches reuse the environment.

That makes the normal path one command, but it doesn't remove all prerequisites. Python must already exist. First setup needs internet access to download packages. Package compatibility, installation permissions, and antivirus behavior still need a real target-machine test.

The bootstrap invokes our new Start CLI command. That command prompts for missing client and quarter, generates the draft, prints verification status, and starts the local review server.

We ask the operating system for an available port instead of assuming a particular port is free. The server binds first, then we construct the URL using its actual port and ask the default browser to open it.

If browser opening isn't available, the URL is printed. If server startup fails, the generated report is preserved and the program gives a review fallback. Keep the terminal open while using approval; Control-C stops the local server.

For macOS and Linux, the equivalent entry is Python three point twelve followed by scripts slash launch dot p-y. The bootstrap chooses the correct virtual-environment interpreter path for the operating system.

The end-to-end server smoke test hit the sandbox's permission restriction in our local coding environment, and the subsequent permission request wasn't approved. That's not proof the launcher works fully, and it's not proof it won't work on a normal machine. The honest status is that unit tests pass and full launch behavior still needs verification.

We're intentionally postponing that testing at your request. We're not running more tests while preparing this listening script.

This is what ease of use means here: fewer setup steps, understandable prompts, automatic handoff, and failure messages that preserve useful work. It isn't measured by whether we can name a cloud tool.

[Pause.]

## Chapter 18: Every Code and Support File Has a Job

Let's do a complete file tour, but connect each filename to its responsibility rather than reciting syntax.

Inside the PMR package, init dot p-y marks the package. Main, spelled with double underscores, is the command-line entry point. It parses Generate, Review, and Start commands, loads environment settings, and reports controlled source-discovery failures.

Config handles local credential loading. Ingest handles discovery and label-based reading. Finance handles deterministic rules and committee state. Evidence handles fact records, formulas, matches, issues, checks, and hashes.

Models handles provider requests, time budgets, response caching, and source-verified quotation selection. Narrative gathers manager support, extracts slides and images, and reads allocation history.

Template inspects reusable prior-report styling and section order. Report builds the shared report model, workbook charts, and PDFs. Review exposes evidence, constrained chart corrections, and approval. Pipeline coordinates the complete run and writes its artifacts.

Those are the application modules. Their separation is functional, not an attempt to build a large framework.

Now scripts. Verify Repeatability launches independent runs and compares hashes. Build Write-up renders our written rationale into a two-page PDF. Package Submission builds a deterministic ZIP with an explicit allowlist and fixed archive timestamps. Launch is the new setup-and-start bootstrap.

The packaging allowlist is important. It includes code, relevant inputs, tests, documentation, selected output artifacts, and the safe environment template. It excludes actual keys, virtual environments, caches, and scratch material. Your study folder is not in the included roots.

Start dot c-m-d is the Windows wrapper. Requirements lists exact direct and transitive package versions. Pyproject defines the project metadata, package discovery, and pytest configuration. Gitignore keeps local credentials and generated environments out of ordinary Git tracking.

The dependency list includes PyMuPDF, openpyxl, ReportLab, Matplotlib, Pillow, pytest, and python-dotenv. Pillow supports image handling. Several remaining packages are dependencies of those tools, not separate architecture components. NumPy supports numerical work under Matplotlib, for example. Pinning transitive dependencies reduces installation drift, but cross-platform compatibility still needs testing.

The GitHub verification workflow is under dot-github slash workflows. As we said, it's a runnable plan for continuous integration, not a verified result until executed.

The six test files are Finance, Pipeline, Models, Template, Config, and Launcher. Each focuses on the boundary suggested by its name.

Readme contains our quick start followed by the original assignment. Spec contains the original rulebook. Running is the implementation run guide: prerequisites, environment keys, commands, review, artifacts, verification, architecture, and limitations.

Docs slash Write-up is the source for the required short rationale. Docs slash Walkthrough gives a compact demonstration plan, business glossary, and questions to practice. This podcast script is your separate extended study material.

Finally, output artifacts. Report dot PDF is the current draft. Review dot HTML is the local evidence interface. Draft dot JSON contains report data, sections, ledger, source hashes, and the draft hash. Evidence dot JSON contains the structured provenance ledger.

Verification dot JSON records checks, issues, selected roles, hashes, model identity, calls, and usage. Repeatability dot JSON records the comparison runs. Test Results XML is a machine-readable test report; like any saved artifact, it needs refreshing when the tested revision changes.

The Assets folder contains extracted deck images and generated workbook charts. The Cache folder holds model responses locally and isn't included in the submission. Appendix dot PDF is a copy of the supplied flash for the review and finalization path.

Write-up dot PDF is the two-page explanation. Vectera PMR Submission dot ZIP is the packaged handoff. Final Report, Approval, Final Evidence, and Final Sections are produced only after successful approval; they are not present in the current no-key output.

You don't need to memorize every filename at the gym. Remember the categories: inputs, extraction, finance, evidence, model assistance, presentation, review, verification, and packaging.

[Pause.]

## Chapter 19: What We Learned While Building It

Several implementation choices came from reading the spec carefully rather than following the previous report blindly.

One example: the prior attribution table doesn't include every role the spec requires, even though its prose identifies a relevant position. We follow the spec by including every selected role. That disagreement belongs in the write-up.

Another example: similar-looking return series can differ. We follow the designated Funding Status and Annual Returns sources for the specified summary, compliance, and annualized chart purposes. We don't force independent market indices to match the custom benchmark.

Another: foreign fund classification and foreign property exposure differ. We show each for its stated purpose and explain the distinction.

Another: approvals can disappear from open totals for a legitimate reason. We report withdrawals and lapses as activity rather than quietly dropping previously announced commitments.

Another: selection must not depend on supporting-document availability. Meridian still appears as a major detractor. We report what the flash proves and explicitly withhold unsupported asset-level explanation.

We also learned that an apparently small rendering bug can materially affect usability. Template typography selection needed adjustment. The review page's JavaScript needed careful string escaping. The layout needed changes for narrow windows so the evidence panel remained reachable.

These are ordinary engineering details, but they matter in a live evaluation. A theoretically correct architecture is not enough if the reviewer can't inspect the result.

Comments and docstrings document module ownership and non-obvious decisions: why capital flows are excluded from attribution, why API failures retain a draft, why initial extraction can't be replaced by manual transcription, why font statistics are weighted, and why installation markers are written only after success.

We avoided commenting every obvious assignment statement. Good comments explain intent or an important constraint, not merely repeat the code in English.

The strongest design decisions are the ones connected to a requirement. Not "we used hashing because hashing sounds technical," but "we use a draft fingerprint to reject approval of changed content." Not "we used AI because this is an AI company," but "vision is needed because required data exists only in chart pixels."

[Pause.]

## Chapter 20: Current Status Without Wishful Thinking

Let's be very precise about where the project stands as this script is written.

We have a generated fourth-quarter financial draft. Its current verification artifact records fifty-one out of fifty-one financial checks passing. It includes the derived fund roles, activity, compliance, workbook charts, disclosures, and original flash appendix.

The most recent full local pytest run passed twenty-three tests. Separate no-key process runs have demonstrated repeatable financial results. The one-command launcher exists and is included in the submission ZIP.

The current generated report used no live model provider. Its verification says zero API calls. Seven required chart-image extractions are unavailable and block final approval. The manager-evidence gap is surfaced rather than filled with invented details.

There is no approved final report or approval record yet.

We haven't completed live model extraction on the actual chart images. We haven't established chart-number reproducibility across fresh independent API calls. We haven't observed execution on Windows Eleven. We haven't verified the complete new launcher-to-browser workflow on that target.

We also haven't demonstrated every possible next-quarter or client layout. Our mutation tests are useful evidence, not a substitute for unseen evaluation.

The remaining completion sequence is straightforward: enable a real provider key, evaluate image extraction, compare fresh runs, confirm chart values, inspect final layout, test the target environment and timing, approve the report, and refresh the write-up and submission package to describe the actual verified state.

Don't confuse a packaged draft with a completed assignment. A ZIP can be beautifully organized and still contain an unfinished report.

With more time, we'd improve numeric image validation, chart selection, structured correction controls, policy and entity adapters, broader fixtures, end-to-end money representation, and production-grade authentication and storage.

We should prioritize the gaps that determine acceptance before adding impressive-sounding infrastructure. That is not avoiding ambition. It is putting effort where failure would actually matter.

[Pause.]

## Chapter 21: The Walkthrough Questions You Should Be Able to Answer

Let's practice as though Prashant is on the call.

Question: why didn't you ask the model to generate the entire report?

Answer: because the specification requires reproducible financial calculations and traceable figures. Models have a bounded role in selecting source sentences and extracting image labels. Python owns ranking, filtering, arithmetic, reconciliation, and compliance.

Question: is this RAG?

Answer: it uses retrieved source evidence to ground model tasks, but it doesn't use embeddings or a vector database. Given the small corpus and known workbook contracts, deterministic evidence retrieval is a better fit for authoritative numerical facts.

Question: how do you handle missing documents?

Answer: distinguish supporting evidence from required evidence. A missing manager report permits financial commentary from the flash and produces a warning. Missing required policy, failing financial checks, or unavailable required chart values prevent approval. We don't invent a substitute.

Question: how do you know it's right?

Answer: source-specific authority, cell-level and page-level provenance, financial reconciliation, golden fixtures, mutated-input tests, separate-process comparisons, and review. Live vision accuracy and Windows execution must be demonstrated separately rather than implied by mocked tests.

Question: how do you handle a new quarter?

Answer: client and quarter drive content discovery. Tables are found by labels and grouped headers. Policies come from the prior report. Committee events are processed through the reporting date. Supported prior layout details are reused. We rely on the stated file-and-column contract and flag unsupported changes.

Question: why does a fund with no manager report still appear?

Answer: performance roles come from dollar contributions and NAV in the flash. Document availability doesn't control selection. We include the role and figures, and explicitly withhold unsupported narrative drivers.

Question: what does approval mean?

Answer: the reviewer inspected the draft, confirmed image readings, and the application checked draft integrity, unchanged sources, and blockers before generating final artifacts. It's a local supervised workflow, not an authenticated institutional sign-off system.

Question: why Python and these libraries?

Answer: they fit the required runtime and document types. Openpyxl reads Excel without Excel. PyMuPDF is an approved parser and handles PDF text, style inspection, and appendices. Matplotlib creates deterministic workbook charts. ReportLab creates portable PDFs. The remaining infrastructure is intentionally small.

Question: what would you improve next?

Answer: first finish live chart evaluation and Windows verification. Then broaden adapters and tests, strengthen image schema and numeric validation, improve review ergonomics, and add authentication and durable audit storage if moving beyond a local prototype.

Question: did you use coding AI?

Answer honestly: yes. The assignment explicitly permits it. Explain which architectural decisions you understand, what you checked, which tests challenge the implementation, and what remains unverified. Don't pretend you manually authored every line or claim capabilities you can't demonstrate.

The goal is not to memorize a polished defense. It's to understand enough that you can answer a follow-up, find the responsible module, and recognize when a question exposes a real limitation.

[Pause.]

## Chapter 22: Final Recap

Let's close with the whole system one more time.

The client and quarter identify the report.

Discovery finds the appropriate sources and ignores distractions.

Parsers turn workbooks, PDF pages, slide text, and chart images into evidence.

Deterministic code calculates contributions, ranks funds, processes committee state, checks compliance, and reconciles the numbers.

AI helps select verified quotations and read image labels. It doesn't decide the math.

The evidence ledger connects facts and calculations to sources.

A shared report model becomes a PDF and an inspectable review interface.

A human checks image readings and warnings. Approval is conditional on integrity checks and the absence of blockers.

Tests and repeated runs challenge the assumptions. Packaging and the one-command launcher make the system easier to hand over.

The project is not finished until live chart accuracy, repeatability of all meaningful figures, target-machine execution, final review, and final artifacts are actually verified.

And the most important sentence to take into the interview is this: "I separated what the system can calculate exactly from what it must interpret, preserved evidence for both, and made finalization depend on explicit checks and human review."

If you understand that sentence and can connect it to the modules, you're no longer just presenting code that AI helped generate. You're explaining an engineering system and the judgment behind it.

That's the point of this assignment. And that's the understanding we're building.

---

## Optional Reference Notes: Not Narration

The implementation descriptions above are grounded in this workspace's source and output artifacts. These primary documentation links support the short conceptual explanations, not a claim that our untested paths work:

- Retrieval and semantic-search background: [OpenAI Retrieval Guide](https://developers.openai.com/api/docs/guides/retrieval). The current project does not use that hosted retrieval implementation.
- PDF text and reading-order background: [PyMuPDF Text Recipes](https://pymupdf.readthedocs.io/en/latest/recipes-text.html).
- Excel reading and cached formula values: [openpyxl Tutorial](https://openpyxl.readthedocs.io/en/stable/tutorial.html).
- Hash function background: [Python hashlib Documentation](https://docs.python.org/3/library/hashlib.html).

Use README.md and SPEC.md for the original assignment, RUNNING.md for current launch instructions, and the actual source for implementation details. Read this script as a snapshot, not as a substitute for subsequent verification.
