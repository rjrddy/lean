# Lean interview

## Two-minute pitch

Lean wraps explicit tool calls with inspectable policies: deduplication, bounded token truncation, structured diagnostic selection and read-only caching. The Python and TypeScript implementations use the same public BPE tokenizer, with parity tests and visible omission markers. A simplest-patch instruction is opt-in. Separate code and manifest signals identify diff growth, new imports, declared dependencies and potentially unused abstractions.

I built the evaluation before claiming savings. A public small model actually selects patches for synthetic coding bugs, and each chosen patch executes against fixture assertions. All policies face paired tasks and candidate orders. The report keeps every outcome, raw prompt, token count and failed check. The model always selected candidate A; its low success and identical selections make the flat success curve weak evidence. Shorter context is measured; preservation of generally useful coding behavior is not established.

The React journal puts that caveat next to the token reduction. It distinguishes retained model inference from a live policy lab that actually compresses text and demonstrates read-only cache behavior. Optional prices are user-entered scenarios; realized dollars remain unknown. A promotion gate refuses a broad cost-saving claim without stronger success and billing evidence. A test also caught structured summarization deleting a source body; I fixed both SDKs and reran the actual experiment. This is a defensible partial project, not a claim to have solved autonomous-agent efficiency.

## Ten-minute walkthrough

Start at `policy.py`: public tokenizer loading, explicit policy data, omission markers, BPE-budget truncation and tagged blocks with indented continuations. Show why a line-based heuristic can lose semantics, including repeated votes and untagged requirements. Walk through the retained source-body regression and its new failing-then-passing test.

Trace the cache from key to admission: scope, tool/version, canonical arguments, explicit read-only flag, TTL after completion, eviction and payload bounds. A read-only function can still change, so the caller controls identity/data revision. Cache exceptions do not become successful results. Cache hits re-filter raw output and still enter context if the application appends them.

Open the TypeScript middleware and real-BPE parity test. Explain the injected tokenizer and trusted plugin function, async overlap rejection, and why a Python caller must serialize access. Do not promise byte-for-byte parity for every Unicode edge case or share these keys as a distributed cache format.

Show `complexity` and `dependency_delta`: AST reference heuristics, diff counts, actual manifest comparisons, and false positives for exports/dynamic references. The tool reports evidence rather than deleting abstractions or pretending to judge architectural quality.

Open `evaluate.py`. The actual pinned public model receives full chat-template prompts and uses a constrained candidate-label decoder. Trusted patches run in fresh isolated-mode subprocesses. Seeds permute candidate order, while policy order is counterbalanced. This is patch selection, not autonomous repository editing, and repeated orders do not create independent task samples.

Use the report to compare all policies, inspect a selected failing patch, enter and clear a hypothetical price, then apply the live filter. End with raw samples, exact environment and weight hash, semantic controls and the nonzero promotion gate. Explain why the current low-competence study cannot justify deployment as a successful cost-saving agent policy.

## Five tradeoffs

- Deterministic filters are inspectable and cheap compared with model summarization, but they can discard the important condition.
- Explicit read-only caching makes side-effect assumptions visible, but freshness and identity remain caller responsibilities.
- A vendored tokenizer gives offline reproducible counts, but those counts are model-specific and are not a provider invoice.
- Constrained patch selection makes correctness checks executable, but it understates the difficulty of open-ended coding agents.
- A retained report makes the default demo lightweight, but it must clearly distinguish archived inference from live filtering.

## Five failure modes

- A critical tail assertion disappears under truncation: the omission marker and executable loss control expose it; the policy is not lossless.
- Repeated results carry multiplicity: deduplication changes the majority control, so cache/dedupe cannot be treated as universally semantics-preserving.
- A summary drops an indented source body: a recorded failing test caught this; block-preserving fixes and a fresh model run are retained.
- Cached read-only data becomes stale: TTL bounds age only under an explicit identity/version contract; mutations and unsuitable reads must bypass caching.
- A weak model makes the same bad choices under every policy: report low success, retain all outcomes, and reject the broad effectiveness claim instead of treating equality as proof.

## Fifteen likely questions

1. **What was actually measured?** Real local model patch-selection outcomes and prompt BPE tokens, plus middleware timings, semantic controls and live lab behavior. See raw outputs and the generated README for exact values.
2. **Is it a coding agent?** The measured harness selects among fixed trusted coding patches. It does not autonomously edit a repository or run arbitrary tools.
3. **Why no dollar claim?** No provider invoice or local electricity/amortization measurement exists. User-entered rates are scenarios only.
4. **Does equal success prove safety?** No. This model has low competence and the same choices across policies, so equality is especially uninformative.
5. **Why use actual BPE?** Character counts and whitespace estimates are not model tokens. Both SDKs share public tokenizer data and measured parity fixtures.
6. **What does caching save?** Read-only tool executions. Repeated model context still costs tokens unless the caller explicitly changes its prompt construction.
7. **What makes a key safe?** Explicit run/identity/data revision scope, tool version and canonical arguments; the caller must encode all relevant state.
8. **Are read-only tools always safe to cache?** No. They can be time-sensitive or identity-dependent. This is a caller contract with TTL, not inferred safety.
9. **What does the summary guarantee?** Selected tagged blocks and their indented continuations are retained, with an omission marker. Untagged conditions can still be lost.
10. **What was caught by a gate?** The source-body regression has a real failing test; the promotion gate also exits nonzero on insufficient competence/cost evidence.
11. **Are complexity signals reliable?** They are inspectable heuristics. Exported entrypoints and dynamic references produce false positives; manifests identify declared packages separately from imports.
12. **How are policies pluggable?** Serializable presets plus trusted custom filter callbacks in both SDKs. The public API accepts preset names, not executable plugins.
13. **Is the UI inference live?** No. It labels actual retained inference separately from live compression/cache requests.
14. **Is Stepwise integrated?** No. Both projects retain gaps, and the instruction requires independent passes before integration. Existing code remains untouched.
15. **What keeps the project partial?** Autonomous-agent effectiveness and realized dollars are unproven; the fixed small-model study is deliberately narrow, and no hosted service is deployed.

## What I would do with three more months

Use a more capable model with a preregistered set of open-ended coding tasks and held-out repositories. Measure real tool trajectories, billable usage and electricity separately; publish paired task outcomes, regressions and uncertainty. Add context-version invalidation and persistent telemetry, then a production threat model and identity layer. Only after independent checks pass, review a Stepwise importer and preserve trace provenance rather than silently treating recorded responses as fresh model evidence.
