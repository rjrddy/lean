# Mark lossy transformations and require read-only cache opt-in

Accepted. Dedupe removes multiplicity; truncation removes tails; structured selection recognizes tagged blocks and indented continuations but can lose untagged constraints. Keep loss markers and executable counterexamples. Cache only explicitly read-only calls, scoped to a run, using versioned canonical arguments and bounded TTL/LRU storage. Read-only is a caller promise, not a guarantee of freshness. Do not count tool cache hits as token savings.
