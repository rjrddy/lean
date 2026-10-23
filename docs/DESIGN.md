# Design: token efficiency is conditional on behavior

The hard part is that a tool result can contain both redundant text and the one condition needed to solve a task. Reducing its tokens is easy. Establishing that the agent still succeeds, and that a bill actually falls, requires separate evidence. Lean keeps those observations separate rather than turning a shorter string into a productivity claim.

## Explicit middleware

Python `Middleware.call` and async TypeScript `Middleware.call` wrap a caller-supplied tool function. A policy chooses identity, stable line deduplication, tagged structured selection, or BPE-budget truncation. The balanced preset combines structured selection, read-only caching and a simplest-patch instruction. Policy data is serializable; callers can inject their own filter callback. Plugins are trusted application code, never supplied through the HTTP API.

Deduplication adds an omission marker because losing multiplicity can change meaning. Structured selection recognizes diagnostic/source/assert/result/error tags and their indented continuation lines. Identical complete blocks are deduplicated. Unknown formats pass through, and unrecognized sections may be discarded when recognized sections exist. This is deterministic extraction, not an LLM summarizer or a proof of semantic equivalence. A test caught source-body loss in an earlier implementation; the failing run, original evaluation and corrected implementation are retained.

Truncation keeps a prefix and an explicit loss marker inside the configured BPE token budget. It is intentionally aggressive. It can remove a critical final assertion. Token counts include the marker. The vendored public tokenizer enables offline Python and TypeScript parity checks; counts refer to that model's BPE, not arbitrary provider billing.

## Cache safety contract

A cache instance belongs to an explicit run/scope. Keys include scope, tool name, tool version and canonical JSON arguments. Only tools explicitly marked read-only are eligible. The caller must include relevant authorization identity and data revision in scope/arguments/version; read-only does not mean immutable. This is a trusted caller contract, not inferred safety or tenant authorization.

TTL starts after tool completion and uses a monotonic clock. Expired entries are removed, access updates LRU order, and entry count plus stored raw-result bytes are bounded. Key/interpreter/tokenizer overhead is outside the payload byte budget. Exceptions, invalid outputs and oversized values do not cache. A cache hit still re-filters the raw result, so a custom plugin must tolerate repeated calls. Cached repeated results still enter the model prompt when the application appends them: caching saves tool work, not automatically context tokens. One caller per middleware instance; Node rejects overlap, Python is synchronous and not thread-safe. Cross-language Unicode sorting/canonical JSON are not a shared distributed cache contract.

## Behavioral constraints and complexity signals

The simplest-patch instruction is an explicit string the application appends to its model system message for the balanced preset. It is an instruction, not an enforced verifier. The actual experiment includes its token overhead.

Python AST inspection reports changed-line counts, newly introduced import names and definitions without local lexical references. A separate manifest comparison reports added/removed/changed declared dependencies in package.json or pyproject.toml. Imports are not package declarations. These are explainable signals, not an over-engineering classifier: exported entrypoints, dynamic imports, decorators and indirect references can produce false positives. There is no automatic patch rejection, dependency removal or code execution from a UI submission.

## Fixed paired model experiment

The public pinned SmolLM model runs locally on CPU. Each fixture asks it to choose among trusted Python patches for a small synthetic bug. Candidate order is seeded. The same task/order is paired across every policy; policy execution order is counterbalanced. Multiple seeds vary order, not the underlying task population. Prompt tokens include system instructions, tool results, candidates, and the model's chat template. Every selected patch executes in a fresh isolated-mode Python subprocess against trusted fixture assertions with a timeout. Arbitrary user code never executes.

The decoder chooses the largest next-token logit among the candidate-label tokens. It is a constrained label decoder, not free-form code generation, repository editing or an autonomous agent. Selected output usage is the label token, not a provider-reported invoice. The report retains raw prompts, logits, chosen/expected labels, failing test output, per-trial token counts, inference time and complexity signals.

The recorded model has low success and makes the same selections across policies. Consequently equal success counts do not establish useful coding competence or safe filtering. Repetitive synthetic diagnostic logs favor compression, so reductions do not generalize to realistic tool streams. No significance interval is inferred from repeated candidate permutations. The complete curve includes every policy, with no selected-only summary. Deterministic semantic controls separately demonstrate harms; they are explicitly not observed model regressions.

A configured promotion gate rejects claiming demonstrated cost-saving agent behavior when observed success is below the requested minimum, paired regressions exist, or realized dollar cost is unknown. Its retained nonzero exit is expected evidence. This gate checks recorded evidence; it is not a statistical safety proof.

## Cost and evidence

Local model inference has no provider invoice. Electricity, hardware amortization and realized dollar savings are not measured. The cost helper leaves actual cost null. Optional user-entered rates produce labelled scenarios only; the UI's scenario input-cost column excludes output and infrastructure cost. There are no built-in invented prices or company adoption claims.

The short benchmark measures real BPE transform costs, bounded read-only caching, semantic loss controls and a recount of every archived prompt against the pinned chat template. It does not rerun inference. `make models eval` runs the actual model experiment with separate optional heavyweight dependencies. Default CI verifies middleware, SDK parity, executable fixtures and archived evidence, excluding that longer inference run. Model measurements identify their actual separate Python environment and public weight hash. The model result's scope, not infrastructure CI, determines what can be claimed.

## Report application and security

React renders a journal-style experiment report with a full scatterplot/table, task-level selected patches, optional scenario rates, and a live text compression/cache lab. Archived inference is labelled separately from live lab work. The lab never calls the model or executes submitted text. Each request creates its own cache; it is an inspectable synthetic demonstration, not a persistent service cache.

The HTTP service defaults to loopback. Binding elsewhere requires a long environment token. The UI keeps it only in memory, API errors are generic, logs include operation/status but no bodies or tokens, requests have a body limit and socket timeout, and browsers face same-origin checks and a restrictive CSP. The threaded development server is single-user tooling, not multitenant hosted infrastructure. No rate limiting, SSO, persistent state, billing integration or production threat-model validation is claimed.

## Stepwise integration

No integration is active. The prior instruction permits integration only after both projects independently pass; Stepwise and Lean retain partial gaps. A future separately reviewed importer can consume redacted Stepwise call data, retain its provenance, and attach measured token counts. Importing an observation does not imply that a replayed model can solve a coding task. Existing repositories remain untouched.

Primary sources: [public model card and license](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct), [official generation semantics](https://huggingface.co/docs/transformers/main/en/main_classes/text_generation), [Observable dot marks](https://observablehq.github.io/plot/marks/dot). The last informs chart design only; this UI uses original SVG/CSS and no copied templates.
