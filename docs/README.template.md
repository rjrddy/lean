# Lean

Agent tool outputs can waste context or hide critical constraints; Lean measures explicit filtering policies against paired synthetic coding-patch tasks.

## Result

Actual local SmolLM inference: $trials decisions; summary input tokens $before → $after ($reduction% fewer); baseline and summary both $passes/$tasks checks passed—a weak model result, **not evidence of preserved autonomous coding ability** ([raw experiment](docs/results/evaluation.json)).
$tests tests pass; $controls executable semantic-loss controls expose harm; $cache_requests repeated read-only requests invoke the tool $cache_calls time ([gates](docs/results/gates.txt), [samples](docs/results/bench.json), [promotion rejected](docs/results/rejected-promotion.txt)).
Summary filtering median $summary_us µs for the synthetic report; actual UI recording $duration s ([browser proof](docs/results/browser/review.json)); realized dollar savings **not measured**.

## Architecture

```mermaid
flowchart LR
    T[Explicit Python / TypeScript tool calls] --> C[Scoped read-only TTL/LRU cache]
    C --> P[Pluggable filter / omission markers]
    P --> M[Actual local constrained model decoder]
    M --> X[Trusted patch fixture checks]
    X --> R[Raw paired outcomes / prompt tokens]
    R --> U[React experiment report]
    U --> L[Live compression and cache lab]
    L --> P
    R --> G[Evidence promotion gate]
```

## Run it

Python and Node/npm required. The default demo uses a vendored public tokenizer and retained actual inference evidence plus live filtering; it downloads no model weights and needs no account. Open http://127.0.0.1:8092.

```sh
make demo
make lint test bench
make models eval  # Optional: install/download the pinned public model and rerun actual inference.
```

[SDK examples](docs/SDK.md) · [Recording steps](docs/DEMO.md) · [Actual video](docs/results/browser/demo.webm) · [Original UI references](docs/UI_REFERENCES.md)

## Decisions and limits

**Partial for the full proof.** This implements the filters, scoped cache, simplest-patch constraint, Python AST/diff/dependency-manifest signals, both SDKs, real paired inference and a React report. The measured model chooses among trusted patches rather than autonomously writing code. It always selected candidate A, regardless of policy, and succeeds poorly. Equal observed counts do not demonstrate useful agent effectiveness. A configured promotion gate exits nonzero on insufficient success and missing dollar evidence.

$curve

Input tokens include the whole model chat template, instructions, tool context and candidates. Seeds permute the same fixed tasks; they are not independent task samples. The decoder ranks candidate-label logits rather than generating unrestricted code. Synthetic reports contain repeated noise that favors compression. No provider invoice, electricity/amortization cost, realized dollars, hosted performance or general coding-agent benefit is measured. Optional UI prices are user assumptions for an input-cost scenario, not a billing claim.

Compression is lossy. Deduplication can change a majority count; truncation can lose the final assertion; structured selection can lose an untagged condition. These executed controls are **not model regressions**. [A real failing test caught source-body loss](docs/results/caught-summary-source-loss.txt); both SDKs were fixed and the full model run repeated. The [original experiment](docs/results/evaluation-before-source-fix.json) remains available.

Caching requires explicitly read-only tools and caller-provided identity/data revision scope. It saves tool executions, not repeated model-context tokens. TTL, entry and raw-payload byte bounds do not include interpreter/key/tokenizer memory. Plugin functions are trusted application code. Complexity signals have false positives for exports/dynamic uses and never automatically rewrite code.

The UI labels recorded inference separately from live lab requests. It supports the complete curve, actual task-level patches/failing checks, optional scenario rates and editable compression/cache inspection. Its default live lab performs no model inference. [Design and guarantees](docs/DESIGN.md) · [ADRs](docs/adr/) · [Quality report](docs/QUALITY.md).

No Stepwise integration is active: the user requires both sides to pass first, and both retain gaps. No existing project was modified, no old repository deleted, no account created and nothing deployed. Docker and Render free-plan templates are prepared only.

[Interview walkthrough](INTERVIEW.md) · [Hard follow-ups](DRILL.md) · [Migration provenance](docs/migration/lean.md) · [CI](https://github.com/rjrddy/lean/actions)

## Next

A preregistered held-out set of open-ended coding tasks with a capable model and actual billed usage; publish paired regressions and uncertainty. Add context-version invalidation, policy shadow mode and stronger identity/ingest controls. Review a provenance-preserving Stepwise importer only after independent acceptance checks pass.
