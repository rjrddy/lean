# Explicit tool middleware

Python:

```python
from lean.policy import Middleware, Policy, Tool, SIMPLE, cost
policy = Policy('my-policy', mode='summary', cache=True, simple=True)
run = Middleware(policy, scope='synthetic-user:run:dataset-revision')
result = run.call(Tool('tests.read', version='fixture-v1', readonly=True),
                  {'path': 'synthetic'}, lambda args: '[RESULT] passed\n[INFO] noise')
# Append result['text'] to the model context. If policy.simple, add SIMPLE to system instructions.
# An assumed rate is a scenario, not actual billed cost:
scenario = cost(result['after_tokens'], 1, input_per_million=2, output_per_million=3)
```

The example rates are caller assumptions, not a provider price or a result. Default cost leaves both actual and scenario dollars unknown. Callers control whether a tool truly is read-only and must encode relevant identity/data revisions in scope, arguments or tool version. Do not cache tools with side effects or time-sensitive reads without considering staleness.

TypeScript exports `Middleware`, `Policy`, `Tool`, `Tokenizer`, `transform` and `SIMPLE` from sdk/typescript/index.ts. Inject a tokenizer exposing `encode(text): number[]` and `decode(ids): string`. The real test uses @huggingface/tokenizers and the vendored public files:

```typescript
const middleware = new Middleware(policy, 'synthetic-user:run:revision', tokenizer);
const result = await middleware.call(
  {name:'tests.read',version:'fixture-v1',readonly:true}, {},
  async () => '[RESULT] passed\n[INFO] noise'
);
```

Python accepts `filter_fn=` and TypeScript accepts a final constructor `filterFn` argument for a custom trusted filter using the same result shape. One caller per instance. A plugin is application code, not a downloadable or UI-executable script. Both SDKs transform cached raw results again; caching does not remove repeated context messages. The standalone Python complexity/dependency helpers report inspectable signals without editing or executing user code.
