# Architecture and Trust Boundaries

```text
client + quarter
      |
      v
content discovery -----> accepted/ignored/failed file decisions
      |
      +-- workbooks ---> exact Decimal finance ---> footing/roles/IC/compliance
      |
      +-- PDFs -------> registered source passages
      |                       |
      |                       +--> bounded evidence agent --> validated claims/trace
      |                            list -> search -> inspect -> validate -> finish/escalate
      |
      +-- deck images -> pinned API vision -> schema/units/bounds/uncertainty
      |
      v
cross-source checks + deterministic financial templates/source excerpts
      |
      v
shared report model --> draft PDF + claims/evidence/semantic manifests
      |
      v
local evidence review + stage/call/cache diagnostics
      |
      v
human correction + confirmation + acknowledgment
      |
      v
backend hash/blocker/schema gate --> approved PDF + final manifests
```

## Deterministic Authority

The flash owns portfolio money, attribution, rankings, returns and weighted LTV. The prior PMR owns policy and reusable style. IC logs own approvals and their state through quarter-end. Rounded manager statistics corroborate; they never replace flash values. Market indices are not the client benchmark. Currency values are finite Decimal amounts at cent precision, serialized as strings. Supporting-document rounding and chart approximation are declared separately from exact monetary identities.

## Agent and Retrieval

This is one small model-directed investigator inside a controlled reporting workflow. The model picks tools and receives their results and rejection feedback. Registered source IDs are the only addressable evidence; arbitrary file paths, shell access, financial overrides and release approval are not tools. Tool schemas, an action limit, repeated-action detection and a shared time budget constrain it. A missing key or model failure preserves source-only output. It is not a free-running multi-agent analyst.

Retrieval is entity-scoped keyword ranking over a small, automatically parsed passage registry. Heading and entity resolution do the heavy lifting. A vector database would add setup without improving the authoritative financial path. The retrieval boundary can be replaced by the company's shared RAG engine without replacing the calculator or approval validator; that integration is not implemented here.

The agent's validated focus quotes feed grounded synthesis. A matching narrative must cite focus evidence. Every sentence names a source; the host attaches its exact quote, and any narrower model-supplied quote is checked verbatim. Source numbers are masked into placeholders and restored by code. Slots must appear exactly once and belong to the sentence's cited passage; raw numbers, altered signs/units and omitted asset names are rejected. Reordering for natural prose is allowed, not a different numerical inventory. Verified citation presence is not proof of entailment, so a separate model checks meaning and human review remains required. Unknown headings and unmatched names receive distinct warnings, not false absence claims. Chart extraction remains a probabilistic numerical boundary with mandatory confirmation. Corrections rebind market slots; changes invalidating the cited conclusion fail closed.

## Verification and Operations

`manifest.json` links report blocks to facts, locators and recursive calculation inputs. Attribution also has per-cell evidence. `semantic_manifest.json` includes all chart observations, financial facts, fund ordering/roles, compliance and structure. Fresh-process comparison fails when these change; changes in diagnostic wording alone are allowed. Code revision hashes prevent a comparison across different implementations.

`diagnostics.json` and the review panel expose measured stage durations, calls, returned token usage, cache hits/misses, failures, issue counts and action observations. They contain no credentials, prompts containing keys, or chain-of-thought. No hosted observability service is required.

Finalization checks unchanged source/exhibit/draft hashes, all chart confirmations, valid reasoned corrections, explicit acknowledgment and no blockers. This is a local integrity workflow, not authentication, a cryptographic signature, or protection from a malicious filesystem owner.
