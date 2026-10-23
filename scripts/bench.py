"""Short, repeatable middleware measurements and explicit semantic-loss controls."""

from __future__ import annotations

import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from lean.policy import POLICIES, Middleware, Tool, tokens, transform
from lean.tasks import tasks

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = tasks()[0]["context"]
    samples = {}
    for policy in POLICIES:
        times = []
        for _ in range(100):
            start = time.perf_counter_ns()
            result = transform(source, policy)
            times.append((time.perf_counter_ns() - start) / 1000)
        samples[policy.name] = {
            "p50_us": statistics.median(times),
            "samples_us": times,
            "before_tokens": result["before_tokens"],
            "after_tokens": result["after_tokens"],
        }
    # Actual counterexamples to lossless compression claims. Do not label as model outcomes.
    repeated = "ALLOW\nALLOW\nDENY"
    modified = transform(repeated, POLICIES[1])["text"]

    def majority(text: str) -> bool:
        return text.splitlines().count("ALLOW") > text.splitlines().count("DENY")

    critical = "[INFO] harmless\n" * 80 + "[ASSERT] empty input must return zero"
    trimmed = transform(critical, POLICIES[4])["text"]
    summary_source = (
        "[RESULT] tests completed\nCritical untagged condition: preserve Unicode casefold"
    )
    summarized = transform(summary_source, POLICIES[2])["text"]
    controls = {
        "dedupe_changes_majority": {"before": majority(repeated), "after": majority(modified)},
        "truncate_loses_tail_assertion": "empty input" not in trimmed,
        "summary_loses_untagged_contract": "Unicode casefold" not in summarized,
        "basis": "deterministic semantic controls, NOT observed model regressions",
    }
    assert controls["dedupe_changes_majority"] == {"before": True, "after": False}
    assert controls["truncate_loses_tail_assertion"] and controls["summary_loses_untagged_contract"]
    cache = Middleware(POLICIES[-1], "bench-readonly")
    for _ in range(100):
        cache.call(Tool("report", "1", True), {}, lambda _: source)
    archive = json.loads((ROOT / "docs/results/evaluation.json").read_text())
    checked = []
    for row in archive["samples"]:
        # The pinned model's chat template, with explicit system + user messages.
        prompt = "".join(
            f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in row["prompt"]
        )
        prompt += "<|im_start|>assistant\n"
        assert tokens(prompt) == row["input_tokens"]
        checked.append(
            {
                "seed": row["seed"],
                "task": row["task"],
                "policy": row["policy"],
                "recounted_input_tokens": tokens(prompt),
            }
        )
    result = {
        "scope": "real BPE transform cost; no model inference in this short bench",
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "samples": samples,
        "semantic_controls": controls,
        "cache": {
            "requests": 100,
            "tool_invocations": cache.tool_invocations,
            "cache_hits": cache.cache_hits,
        },
        "archive_recount": checked,
        "policies": [asdict(p) for p in POLICIES],
        "source_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("src", "sdk")
            for p in (ROOT / folder).rglob("*")
            if p.is_file() and p.suffix in (".py", ".ts")
        },
    }
    (ROOT / "docs/results/bench.json").write_text(json.dumps(result, indent=2) + "\n")
    (ROOT / "docs/results/caught-failure.json").write_text(json.dumps(controls, indent=2) + "\n")
    rejected = subprocess.run([sys.executable, "scripts/gate.py"], capture_output=True, text=True)
    assert rejected.returncode == 1
    (ROOT / "docs/results/rejected-promotion.txt").write_text(
        "$ .venv/bin/python scripts/gate.py\n" + rejected.stdout + "exit_code=1\n"
    )
    print(
        json.dumps(
            {
                "semantic_controls": controls,
                "cache": result["cache"],
                "archive_prompts_recounted": len(checked),
            }
        )
    )


if __name__ == "__main__":
    main()
