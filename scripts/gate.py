"""Reject promoting this small experiment as a proven cost-saving coding-agent policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="summary")
    parser.add_argument("--minimum-success", type=float, default=0.8)
    args = parser.parse_args()
    if not 0 <= args.minimum_success <= 1:
        raise SystemExit("invalid threshold")
    report = json.loads(Path("docs/results/evaluation.json").read_text())
    candidate = next(r for r in report["summary"] if r["policy"] == args.policy)
    reasons = []
    if candidate["successes"] / candidate["tasks"] < args.minimum_success:
        reasons.append("observed success below configured minimum")
    if candidate["regressions"]:
        reasons.append("paired regressions observed")
    if candidate["actual_usd"] is None:
        reasons.append("realized dollar savings not measured")
    print(
        json.dumps(
            {
                "promote": not reasons,
                "policy": args.policy,
                "minimum_success": args.minimum_success,
                "reasons": reasons,
                "basis": "configured evidence gate, not statistical proof",
            }
        )
    )
    raise SystemExit(1 if reasons else 0)


if __name__ == "__main__":
    main()
