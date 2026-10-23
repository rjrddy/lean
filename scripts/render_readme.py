"""Render numeric claims exclusively from retained command outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template

root = Path(__file__).resolve().parents[1]
r = json.loads((root / "docs/results/evaluation.json").read_text())
b = json.loads((root / "docs/results/bench.json").read_text())
v = json.loads((root / "docs/results/browser/review.json").read_text())
base = r["summary"][0]
summary = next(x for x in r["summary"] if x["policy"] == "summary")
lines = ["| Policy | Input tokens | Reduction | Passed / trials |", "|---|---:|---:|---:|"]
for row in r["summary"]:
    lines.append(
        f"| {row['policy']} | {row['input_tokens']:,} | "
        f"{row['input_token_reduction_percent']:.1f}% | "
        f"{row['successes']} / {row['tasks']} |"
    )
counts = re.findall(r"(\d+) passed", (root / "docs/results/gates.txt").read_text())
values = {
    "trials": len(r["samples"]),
    "before": f"{base['input_tokens']:,}",
    "after": f"{summary['input_tokens']:,}",
    "reduction": f"{summary['input_token_reduction_percent']:.1f}",
    "passes": summary["successes"],
    "tasks": summary["tasks"],
    "tests": counts[-1],
    "controls": len(b["semantic_controls"]) - 1,
    "cache_requests": b["cache"]["requests"],
    "cache_calls": b["cache"]["tool_invocations"],
    "summary_us": f"{b['samples']['summary']['p50_us']:.2f}",
    "duration": f"{float(v['ffprobe']['format']['duration']):.2f}",
    "curve": "\n".join(lines),
}
(root / "README.md").write_text(
    Template((root / "docs/README.template.md").read_text()).substitute(values)
)
