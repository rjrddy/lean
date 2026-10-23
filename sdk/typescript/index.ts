export interface Tokenizer {
  encode(text: string): number[];
  decode(ids: number[]): string;
}
export interface Policy {
  name: string;
  mode: "none" | "dedupe" | "summary" | "truncate";
  limit: number;
  cache: boolean;
  simple: boolean;
}
export interface Tool {
  name: string;
  version: string;
  readonly: boolean;
}
export const SIMPLE =
  "Use the smallest correct patch. Add no dependencies or unused abstractions.";
export function transform(text: string, policy: Policy, tokenizer: Tokenizer) {
  if (new TextEncoder().encode(text).length > 65536)
    throw Error("tool output too large");
  if (
    !["none", "dedupe", "summary", "truncate"].includes(policy.mode) ||
    !Number.isInteger(policy.limit) ||
    policy.limit < 16 ||
    policy.limit > 8192
  )
    throw Error("invalid policy");
  const count = (s: string) => tokenizer.encode(s).length;
  const before = count(text);
  const lines = () => {
    const rows = text.split(/\r\n|\r|\n/);
    if (rows.at(-1) === "") rows.pop();
    return rows;
  };
  if (policy.mode === "dedupe") {
    const rows = lines(),
      unique = [...new Set(rows)];
    const removed = rows.length - unique.length;
    text = unique.join("\n");
    if (removed)
      text += `\n[Lean: removed ${removed} repeated lines; multiplicity lost]`;
  } else if (policy.mode === "summary") {
    const blocks: string[][] = [];
    let current: string[] | null = null;
    for (const line of lines()) {
      if (/^\[(ASSERT|FAIL|SOURCE|RESULT|ERROR)\]/.test(line)) {
        current = [line];
        blocks.push(current);
      } else if (current !== null && /^[ \t]/.test(line)) current.push(line);
      else current = null;
    }
    const selected = [...new Set(blocks.map((block) => block.join("\n")))];
    if (selected.length)
      text =
        selected.join("\n") +
        "\n[Lean: structured selection; other lines omitted]";
  } else if (policy.mode === "truncate") {
    const ids = tokenizer.encode(text);
    if (ids.length > policy.limit) {
      const marker = "\n[Lean: truncated; information lost]";
      let keep = Math.max(0, policy.limit - count(marker) - 2);
      do {
        text = tokenizer.decode(ids.slice(0, keep)) + marker;
      } while (count(text) > policy.limit && keep-- > 0);
    }
  }
  return {
    text,
    before_tokens: before,
    after_tokens: count(text),
    policy,
    changed: count(text) !== before || policy.mode !== "none",
  };
}
function stable(v: unknown): string {
  if (v === undefined) throw Error("JSON only");
  if (typeof v === "number" && !Number.isFinite(v))
    throw Error("finite JSON only");
  if (Array.isArray(v)) return "[" + v.map(stable).join(",") + "]";
  if (v !== null && typeof v === "object")
    return (
      "{" +
      Object.keys(v)
        .sort()
        .map(
          (k) =>
            JSON.stringify(k) + ":" + stable((v as Record<string, unknown>)[k]),
        )
        .join(",") +
      "}"
    );
  return JSON.stringify(v);
}
export class Middleware {
  private entries = new Map<
    string,
    { expires: number; raw: string; size: number }
  >();
  private bytes = 0;
  private busy = false;
  toolInvocations = 0;
  cacheHits = 0;
  constructor(
    public policy: Policy,
    public scope: string,
    public tokenizer: Tokenizer,
    public ttl = 10,
    public capacity = 16,
    public maxBytes = 1000000,
    public clock = () => performance.now() / 1000,
    public filterFn: typeof transform = transform,
  ) {
    if (
      !scope ||
      !Number.isFinite(ttl) ||
      ttl <= 0 ||
      !Number.isInteger(capacity) ||
      capacity < 1 ||
      capacity > 1000 ||
      maxBytes < 1 ||
      maxBytes > 10000000
    )
      throw Error("invalid cache bounds/scope");
  }
  async call(
    tool: Tool,
    args: unknown,
    fn: (args: unknown) => Promise<string>,
  ) {
    if (this.busy) throw Error("one caller per middleware");
    this.busy = true;
    try {
      const key = stable([this.scope, tool.name, tool.version, args]);
      if (new TextEncoder().encode(key).length > 65536)
        throw Error("arguments too large");
      const now = this.clock();
      for (const [k, v] of this.entries)
        if (v.expires <= now) {
          this.entries.delete(k);
          this.bytes -= v.size;
        }
      const cached =
        this.policy.cache && tool.readonly ? this.entries.get(key) : undefined;
      if (cached) {
        this.entries.delete(key);
        this.entries.set(key, cached);
        this.cacheHits++;
        return {
          ...this.filterFn(cached.raw, this.policy, this.tokenizer),
          cache_hit: true,
        };
      }
      this.toolInvocations++;
      const raw = await fn(structuredClone(args));
      const result = this.filterFn(raw, this.policy, this.tokenizer),
        size = new TextEncoder().encode(raw).length;
      if (this.policy.cache && tool.readonly && size <= this.maxBytes) {
        while (
          this.entries.size &&
          (this.entries.size >= this.capacity ||
            this.bytes + size > this.maxBytes)
        ) {
          const oldest = this.entries.keys().next().value!;
          this.bytes -= this.entries.get(oldest)!.size;
          this.entries.delete(oldest);
        }
        this.entries.set(key, { expires: this.clock() + this.ttl, raw, size });
        this.bytes += size;
      }
      return { ...result, cache_hit: false };
    } finally {
      this.busy = false;
    }
  }
}
