# Hard follow-ups

1. **Why isn't a shorter string enough?** The lost text may encode a necessary constraint; semantic controls and task outcomes are separate measurements.
2. **Why can dedupe break voting?** Multiplicity is information. Removing duplicate votes can change the majority even if unique lines stay intact.
3. **What exact summary bug was caught?** Keeping a source heading but dropping its indented function body. The failing assertion and corrected model rerun are retained.
4. **Does the fix preserve every source layout?** No. It understands tagged blocks with indented continuations, not arbitrary logs or every programming language's syntax.
5. **Does truncation include its own marker in the budget?** Yes. The retained prefix shrinks until marker plus content fit the BPE cap.
6. **Can the summary grow the output?** Yes, on small tagged inputs its marker can add tokens. The implementation reports counts rather than guaranteeing reduction.
7. **What is the cache's byte limit?** Stored raw-result payload bytes. Keys, Python/JS objects and tokenizer memory are outside that bound.
8. **When does TTL start?** After successful tool completion, using a monotonic clock. Expiry removes the entry before a subsequent lookup.
9. **What if the tool throws?** The failure propagates and no successful cache entry is inserted.
10. **Does scope enforce authorization?** No. It separates caller-provided contexts; the application must actually authenticate and encode identity/data revision.
11. **Can both SDKs share distributed keys?** Not as a promised format. Unicode canonical sorting and integer representation have cross-language edge cases; instances are local.
12. **Why re-filter cached raw data?** The cache memoizes the tool response. The configured filter/plugin remains the policy boundary, so a plugin must handle repeated calls.
13. **Where is the simplest-first constraint enforced?** It is appended to the balanced preset's system message in the actual evaluation. It is not a code verifier or a guaranteed behavior change.
14. **Are added imports new dependencies?** Not necessarily. A separate manifest comparison identifies declared dependency changes; neither proves runtime necessity.
15. **What does an unused definition mean?** No lexical load of its name appeared in the AST. Exports, reflection and indirect uses can invalidate that signal.
16. **What does a constrained label decoder measure?** The model's choice among candidate patches from next-token logits, not generated code quality or provider-billed usage.
17. **Why not call repeated seeds independent tasks?** They permute the same fixture candidates and cannot justify a larger independent sample size or a population confidence claim.
18. **Why can a flat success curve be bad evidence?** A model insensitive to context can make the same wrong choices after any filter. The report visibly keeps that low-competence caveat.
19. **What does the promotion gate establish?** That the stored evidence satisfies configured conditions. Here it rejects; even passing would not be statistical proof or production safety certification.
20. **Why defer Stepwise integration?** The user's rule requires both sides to pass independently. A working format importer would not close either project's behavioral evaluation gaps.
