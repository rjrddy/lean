import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
type Summary = {
  policy: string;
  tasks: number;
  successes: number;
  input_tokens: number;
  output_tokens: number;
  input_token_reduction_percent: number;
  regressions: string[];
  tool_invocations: number;
  cache_hits: number;
};
type Sample = {
  seed: number;
  task: string;
  policy: string;
  success: boolean;
  choice: string;
  correct_choice: string;
  input_tokens: number;
  selected_patch: string;
  check_stderr: string;
  filtered_tool: { text: string; before_tokens: number; after_tokens: number };
  complexity: {
    added_lines: number;
    added_imports: string[];
    definitions_not_lexically_referenced: string[];
  };
};
type Report = {
  model: string;
  kind: string;
  summary: Summary[];
  samples: Sample[];
  limits: string[];
};
type Fixture = { id: string; context: string };
type Lab = {
  first: { text: string; before_tokens: number; after_tokens: number };
  invocations: number;
  cache_hits: number;
  basis: string;
};
const pretty = (value: unknown) => JSON.stringify(value, null, 2);
const colors = [
  "#253d30",
  "#74915b",
  "#a25b26",
  "#71658d",
  "#b24c55",
  "#526c87",
];
function App() {
  const [report, setReport] = useState<Report | null>(null),
    [policy, setPolicy] = useState("summary"),
    [seed, setSeed] = useState(7301),
    [selected, setSelected] = useState("empty-mean");
  const [fixtures, setFixtures] = useState<Fixture[]>([]),
    [text, setText] = useState(""),
    [lab, setLab] = useState<Lab | null>(null),
    [token, setToken] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [rate, setRate] = useState("");
  async function api(path: string, data?: unknown) {
    const response = await fetch("/api/" + path, {
      method: data === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    const value = await response.json();
    if (!response.ok) throw Error(value.error);
    return value;
  }
  async function task(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function load() {
    const [r, p] = await Promise.all([api("report"), api("policies")]);
    setReport(r);
    setFixtures(p.tasks);
    setText(p.tasks[0].context);
  }
  useEffect(() => {
    void task(load);
  }, []);
  useEffect(() => {
    const fixture = fixtures.find((f) => f.id === selected);
    if (fixture) setText(fixture.context);
    setLab(null);
  }, [selected, fixtures]);
  const current = report?.summary.find((p) => p.policy === policy),
    baseline = report?.summary[0];
  const rows =
      report?.samples.filter((r) => r.policy === policy && r.seed === seed) ||
      [],
    active = rows.find((r) => r.task === selected);
  const scenario =
    rate !== "" && Number.isFinite(Number(rate)) && Number(rate) >= 0
      ? Number(rate)
      : null;
  const maxX = baseline ? (baseline.input_tokens / baseline.tasks) * 1.1 : 1200;
  return (
    <div className="page">
      <header>
        <a href="/" className="logo">
          lean<span>FIELD NOTES ON AGENT EFFICIENCY</span>
        </a>
        <div className="header-right">
          <span className="pill">LOCAL MODEL STUDY</span>
          <a href="https://github.com/rjrddy/lean">SOURCE ↗</a>
        </div>
      </header>
      <section className="hero">
        <div>
          <p className="eyebrow">LESS CONTEXT, MEASURED.</p>
          <h1>
            Cut the noise.
            <br />
            <span>Keep the evidence.</span>
          </h1>
        </div>
        <div className="abstract">
          <p>
            A small experiment in spending fewer tokens.
            <br />
            Every policy faces the same patch-selection tasks.
            <br />
            The failures stay in the report.
          </p>
          <p className="fine">
            Recorded local SmolLM inference · Live policy lab below
            <br />
            No paid API. Dollar savings not measured.
          </p>
        </div>
      </section>
      {error && (
        <div className="error" role="alert">
          {error}
          <button onClick={() => void task(load)}>Retry connection</button>
        </div>
      )}
      <details className="connection">
        <summary>Connection settings</summary>
        <label>
          API token
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            autoComplete="off"
          />
        </label>
        <button onClick={() => void task(load)}>Reconnect</button>
      </details>
      {report && current && baseline ? (
        <>
          <section className="study-top">
            <div>
              <span className="eyebrow">
                EXPERIMENT / FIXED SYNTHETIC PATCHES
              </span>
              <h2>Efficiency has a condition.</h2>
            </div>
            <p className="study-caption">
              A token reduction is useful only if the task still passes.
              <br />
              Select a policy to inspect both sides of the tradeoff.
            </p>
          </section>
          <nav className="policies" aria-label="Filter policy">
            {report.summary.map((p, i) => (
              <button
                key={p.policy}
                aria-pressed={policy === p.policy}
                className={policy === p.policy ? "active" : ""}
                onClick={() => {
                  setPolicy(p.policy);
                  setLab(null);
                }}
              >
                <span className={"policy-dot dot-" + i} />
                {p.policy}
                <span>{p.input_token_reduction_percent.toFixed(1)}%</span>
              </button>
            ))}
          </nav>
          <section className="experiment">
            <div className="plot">
              <div className="plot-label">
                <span>PROMPT TOKENS × TASK SUCCESS</span>
                <span>← less context</span>
              </div>
              <svg
                viewBox="0 0 660 370"
                role="img"
                aria-label="Tradeoff chart showing prompt tokens per task and observed success"
              >
                <rect x="65" y="25" width="550" height="280" fill="#f7f6ee" />
                {[0, 25, 50, 75, 100].map((n) => (
                  <g key={n}>
                    <line
                      x1="65"
                      x2="615"
                      y1={305 - 2.8 * n}
                      y2={305 - 2.8 * n}
                      stroke="#d9dbd1"
                      strokeDasharray="3 5"
                    />
                    <text x="50" y={310 - 2.8 * n} textAnchor="end">
                      {n}%
                    </text>
                  </g>
                ))}
                {[0, 0.25, 0.5, 0.75, 1].map((n) => (
                  <g key={n}>
                    <line
                      x1={65 + 550 * n}
                      x2={65 + 550 * n}
                      y1="25"
                      y2="305"
                      stroke="#d9dbd1"
                      strokeDasharray="3 5"
                    />
                    <text x={65 + 550 * n} y="327" textAnchor="middle">
                      {Math.round(maxX * n)}
                    </text>
                  </g>
                ))}
                <text x="340" y="360" textAnchor="middle">
                  INPUT TOKENS / TRIAL
                </text>
                {report.summary.map((p, i) => {
                  const x = 65 + (p.input_tokens / p.tasks / maxX) * 550,
                    y = 305 - (p.successes / p.tasks) * 280;
                  return (
                    <g key={p.policy}>
                      <circle
                        cx={x}
                        cy={y}
                        r={policy === p.policy ? 11 : 6}
                        fill={colors[i]}
                        stroke={policy === p.policy ? "#253d30" : "#f7f6ee"}
                        strokeWidth={policy === p.policy ? 3 : 1}
                      />
                      {policy === p.policy && (
                        <text
                          x={Math.min(x, 540)}
                          y={y - 23}
                          textAnchor="middle"
                          className="selected-label"
                        >
                          {p.policy}
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>
              <p className="plot-note">
                Paired candidate orders; repeated seeds are not independent
                tasks. Points show observations, not confidence intervals.
              </p>
            </div>
            <div className="finding">
              <p className="eyebrow">
                SELECTED POLICY / {current.policy.toUpperCase()}
              </p>
              <div className="big-number">
                {current.input_token_reduction_percent.toFixed(1)}
                <span>%</span>
              </div>
              <p className="metric-name">fewer input tokens than baseline</p>
              <div className="outcome">
                <strong>
                  {current.successes}
                  <span>/{current.tasks}</span>
                </strong>
                <p>
                  patch trials passed
                  <br />
                  <b>
                    {((current.successes / current.tasks) * 100).toFixed(1)}%
                    observed success
                  </b>
                </p>
              </div>
              <p className="validity">
                A weak result, kept visible. This small model made the same
                selections under every policy. Equal success here does not prove
                useful coding ability was preserved.
              </p>
              <dl>
                <div>
                  <dt>Prompt tokens</dt>
                  <dd>{current.input_tokens.toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Tool calls / cache hits</dt>
                  <dd>
                    {current.tool_invocations} / {current.cache_hits}
                  </dd>
                </div>
                <div>
                  <dt>Actual dollar savings</dt>
                  <dd>not measured</dd>
                </div>
              </dl>
            </div>
          </section>
          <section className="ledger">
            <div className="section-heading">
              <div>
                <p className="eyebrow">THE FULL CURVE</p>
                <h2>Nothing filtered out of the report.</h2>
              </div>
              <label className="scenario">
                Optional scenario input $ / 1M tokens
                <input
                  aria-label="Scenario input rate"
                  inputMode="decimal"
                  value={rate}
                  placeholder="Your assumed rate"
                  onChange={(e) => setRate(e.target.value)}
                />
              </label>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Policy</th>
                    <th>Input tokens</th>
                    <th>Reduction</th>
                    <th>Pass / trials</th>
                    <th>Scenario input $</th>
                  </tr>
                </thead>
                <tbody>
                  {report.summary.map((p) => (
                    <tr
                      key={p.policy}
                      className={policy === p.policy ? "chosen" : ""}
                    >
                      <td>
                        <button onClick={() => setPolicy(p.policy)}>
                          {p.policy} ↗
                        </button>
                      </td>
                      <td>{p.input_tokens.toLocaleString()}</td>
                      <td>{p.input_token_reduction_percent.toFixed(1)}%</td>
                      <td>
                        {p.successes} / {p.tasks}
                      </td>
                      <td>
                        {scenario === null
                          ? "not set"
                          : ((p.input_tokens * scenario) / 1e6).toFixed(6)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="fine">
              Scenario = your assumed input rate × measured token count. It
              excludes output and infrastructure costs and is not an invoice or
              realized savings.
            </p>
          </section>
          <section className="task-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">OPEN THE NOTEBOOK</p>
                <h2>See the patch, not just the score.</h2>
              </div>
              <label>
                Candidate-order seed
                <select
                  aria-label="Candidate-order seed"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                >
                  {[...new Set(report.samples.map((r) => r.seed))].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="task-grid">
              <div className="task-list">
                {rows.map((r, i) => (
                  <button
                    key={r.task}
                    aria-pressed={selected === r.task}
                    onClick={() => setSelected(r.task)}
                  >
                    <span>{String(i + 1).padStart(2, "0")}</span>
                    <b>{r.task}</b>
                    <em className={r.success ? "pass" : "fail"}>
                      {r.success ? "PASS" : "FAIL"}
                    </em>
                  </button>
                ))}
              </div>
              {active && (
                <article className="patch">
                  <div className="patch-title">
                    <h3>{active.task}</h3>
                    <span className={active.success ? "pass" : "fail"}>
                      {active.success ? "CHECKS PASSED" : "CHECKS FAILED"}
                    </span>
                  </div>
                  <p className="fine">
                    Selected {active.choice} · expected {active.correct_choice}{" "}
                    · {active.input_tokens} input tokens
                  </p>
                  <pre tabIndex={0}>{active.selected_patch}</pre>
                  <details>
                    <summary>Test output & complexity signals</summary>
                    <pre>
                      {active.check_stderr || "All fixture assertions passed."}
                    </pre>
                    <pre>{pretty(active.complexity)}</pre>
                    <p className="fine">
                      Lexical references can miss exported or dynamic uses.
                      Signals are not proof of over-engineering.
                    </p>
                  </details>
                </article>
              )}
            </div>
          </section>
          <section className="lab">
            <div className="lab-intro">
              <p className="eyebrow">LIVE POLICY LAB</p>
              <h2>
                Try the filter.
                <br />
                <em>Inspect what goes missing.</em>
              </h2>
              <p>
                Uses the selected task and policy. This live request compresses
                text and repeats a read-only tool call. It does not run model
                inference.
              </p>
              <button
                className="dark"
                disabled={busy}
                onClick={() =>
                  void task(async () => {
                    setLab(await api("lab", { policy, task: selected, text }));
                  })
                }
              >
                Apply {policy} →
              </button>
              <div className="canary">
                <b>Loss controls</b>
                <p>
                  Deduplication can change majority counts. Truncation can drop
                  a final assertion. Structured selection can discard an
                  untagged requirement.
                </p>
                <a href="https://github.com/rjrddy/lean/blob/main/docs/results/caught-failure.json">
                  See executed counterexamples ↗
                </a>
              </div>
            </div>
            <div className="lab-editor">
              <label htmlFor="tool-text">
                TOOL OUTPUT / EDITABLE SYNTHETIC CONTEXT
              </label>
              <textarea
                id="tool-text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                spellCheck={false}
              />
              {lab && (
                <>
                  <div className="lab-receipt" role="status">
                    <strong>
                      {lab.first.before_tokens} → {lab.first.after_tokens}{" "}
                      tokens
                    </strong>
                    <span>
                      {lab.invocations} tool calls · {lab.cache_hits} cache hits
                    </span>
                  </div>
                  <pre tabIndex={0}>{lab.first.text}</pre>
                  <p className="fine">
                    Live filter response. Read-only cache lasts only for this
                    request.
                  </p>
                </>
              )}
            </div>
          </section>
          <section className="limits">
            <span className="asterisk">*</span>
            <div>
              <h3>A small study, not a universal promise.</h3>
              <p>
                Actual local inference, constrained to choosing among trusted
                patch candidates. No autonomous repository editing. Synthetic
                tasks, a small model and a flat low-success curve limit what
                this result says. Realized dollar savings, a paid-provider
                comparison and general coding-agent effectiveness are not
                measured.
              </p>
              <a href="https://github.com/rjrddy/lean/blob/main/docs/DESIGN.md">
                Read the method and limits ↗
              </a>
            </div>
          </section>
        </>
      ) : (
        <p className="loading" role="status">
          {error
            ? "Report unavailable. Check connection settings."
            : "Loading recorded model evidence…"}
        </p>
      )}
      <footer>
        <strong>lean /</strong>
        <span>MEASURED CONTEXT. VISIBLE TRADEOFFS.</span>
        <span>Standalone project · Not deployed</span>
      </footer>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
