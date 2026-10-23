"""Actual local model inference over fixed, executable synthetic patch-selection tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from lean.policy import POLICIES, SIMPLE, Middleware, Tool, complexity, cost
from lean.tasks import tasks

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(ROOT / ".cache/model"))
    parser.add_argument("--seeds", default="7301,7302,7303")
    args = parser.parse_args()
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    torch.manual_seed(7301)
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, local_files_only=True).eval()
    labels = ["A", "B", "C"]
    label_ids = [tokenizer.encode(letter, add_special_tokens=False)[0] for letter in labels]
    assert all(len(tokenizer.encode(label, add_special_tokens=False)) == 1 for label in labels)
    samples = []
    started = time.monotonic()
    for seed in map(int, args.seeds.split(",")):
        fixture_tasks = tasks(seed)
        # Counterbalance policy execution order, retaining the same candidate order per paired task.
        policies = POLICIES.copy()
        random.Random(seed).shuffle(policies)
        for task in fixture_tasks:
            for policy in policies:
                middleware = Middleware(policy, f"{seed}:{task['id']}")
                tool = Tool("test.report", "fixture-v1", readonly=True)
                first = middleware.call(tool, {"task": task["id"]}, lambda _: task["context"])
                second = middleware.call(tool, {"task": task["id"]}, lambda _: task["context"])
                # Repeated tool results remain repeated context: cache saves tool work, not tokens.
                context = first["text"] + "\n" + second["text"]
                system = "Choose the correct Python patch. Reply with A, B, or C only."
                if policy.simple:
                    system += " " + SIMPLE
                user = task["prompt"] + "\nTool reports:\n" + context + "\nCandidate patches:\n"
                user += "\n".join(
                    f"{letter}:\n{code}"
                    for letter, code in zip(labels, task["candidates"], strict=True)
                )
                user += "\nCorrect patch letter:"
                messages = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
                encoded = tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors="pt",
                    return_dict=True,
                )
                call_start = time.perf_counter()
                with torch.inference_mode():
                    logits = model(**encoded).logits[0, -1, label_ids]
                choice = int(torch.argmax(logits))
                elapsed = time.perf_counter() - call_start
                selected = task["candidates"][choice]
                # Only trusted repository fixtures execute, in an isolated fresh Python process.
                check = subprocess.run(
                    [sys.executable, "-I", "-c", selected + "\n" + task["checks"]],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    env={"PATH": os.defpath},
                )
                row = {
                    "seed": seed,
                    "task": task["id"],
                    "policy": policy.name,
                    "success": check.returncode == 0,
                    "choice": labels[choice],
                    "correct_choice": labels[task["correct_index"]],
                    "input_tokens": int(encoded["input_ids"].numel()),
                    "output_tokens": 1,
                    "output_usage_basis": "one constrained label; full-vocabulary generation not run",
                    "inference_seconds": elapsed,
                    "label_logits": logits.tolist(),
                    "tool_invocations": middleware.tool_invocations,
                    "cache_hits": middleware.cache_hits,
                    "selected_patch": selected,
                    "check_exit": check.returncode,
                    "check_stderr": check.stderr,
                    "complexity": complexity(selected),
                    "cost": cost(0, 0),
                    "prompt": messages,
                    "filtered_tool": first,
                }
                samples.append(row)
                print(
                    json.dumps(
                        {k: row[k] for k in ("seed", "task", "policy", "success", "input_tokens")}
                    ),
                    flush=True,
                )
    grouped = defaultdict(list)
    for row in samples:
        grouped[row["policy"]].append(row)
    baseline = grouped["baseline"]
    paired = {(r["seed"], r["task"]): r for r in baseline}
    summaries = []
    for policy in POLICIES:
        rows = grouped[policy.name]
        total = sum(r["input_tokens"] for r in rows)
        base_tokens = sum(r["input_tokens"] for r in baseline)
        summaries.append(
            {
                "policy": policy.name,
                "tasks": len(rows),
                "successes": sum(r["success"] for r in rows),
                "input_tokens": total,
                "output_tokens": len(rows),
                "input_token_reduction_percent": 100 * (1 - total / base_tokens),
                "regressions": [
                    f"{r['seed']}:{r['task']}"
                    for r in rows
                    if not r["success"] and paired[(r["seed"], r["task"])]["success"]
                ],
                "improvements": [
                    f"{r['seed']}:{r['task']}"
                    for r in rows
                    if r["success"] and not paired[(r["seed"], r["task"])]["success"]
                ],
                "tool_invocations": sum(r["tool_invocations"] for r in rows),
                "cache_hits": sum(r["cache_hits"] for r in rows),
                "actual_usd": None,
            }
        )
    model_path = Path(args.model)
    result = {
        "kind": "actual local model constrained patch selection; not autonomous code generation",
        "model": "HuggingFaceTB/SmolLM2-135M-Instruct",
        "model_revision": "12fd25f77366fa6b3b4b768ec3050bf629380bac",
        "model_sha256": hashlib.sha256((model_path / "model.safetensors").read_bytes()).hexdigest(),
        "tokenizer_sha256": hashlib.sha256(
            (ROOT / "assets/tokenizer.json").read_bytes()
        ).hexdigest(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
        "elapsed_seconds": time.monotonic() - started,
        "samples": samples,
        "summary": summaries,
        "actual_usd": None,
        "limits": [
            "local inference cost and provider dollar savings not measured",
            "small fixed multiple-choice fixtures, not autonomous coding tasks",
            "seeds vary candidate order; not independent task samples",
            "three-label logits, not unconstrained model generation",
            "cache reduces read-only tool executions, not repeated prompt tokens",
        ],
    }
    out = ROOT / "docs/results/evaluation.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"summary": summaries, "elapsed_seconds": result["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
