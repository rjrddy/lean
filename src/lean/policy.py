"""Explicit, lossy tool-output filters; token counts use the actual vendored BPE."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import re
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[2]
TOKENIZER = Tokenizer.from_file(str(ROOT / "assets/tokenizer.json"))


def tokens(text: str) -> int:
    return len(TOKENIZER.encode(text, add_special_tokens=False).ids)


@dataclass(frozen=True)
class Policy:
    name: str
    mode: str = "none"
    limit: int = 256
    cache: bool = False
    simple: bool = False

    def __post_init__(self) -> None:
        if self.mode not in ("none", "dedupe", "summary", "truncate"):
            raise ValueError("unknown mode")
        if type(self.limit) is not int or not 16 <= self.limit <= 8192:
            raise ValueError("token limit must be bounded")


POLICIES = [
    Policy("baseline"),
    Policy("dedupe", "dedupe"),
    Policy("summary", "summary"),
    Policy("trim256", "truncate", 256),
    Policy("trim64", "truncate", 64),
    Policy("balanced", "summary", cache=True, simple=True),
]
SIMPLE = "Use the smallest correct patch. Add no dependencies or unused abstractions."


def transform(text: str, policy: Policy) -> dict:
    if not isinstance(text, str) or len(text.encode()) > 65536:
        raise ValueError("tool output must be bounded text")
    before = tokens(text)
    if policy.mode == "dedupe":
        seen = set()
        lines = []
        removed = 0
        for line in text.splitlines():
            if line in seen:
                removed += 1
            else:
                seen.add(line)
                lines.append(line)
        text = "\n".join(lines)
        if removed:
            text += f"\n[Lean: removed {removed} repeated lines; multiplicity lost]"
    elif policy.mode == "summary":
        lines = text.splitlines()
        selected = list(
            dict.fromkeys(
                line for line in lines if re.match(r"\[(ASSERT|FAIL|SOURCE|RESULT|ERROR)\]", line)
            )
        )
        # No recognized structure: preserve instead of silently fabricating a summary.
        if selected:
            text = "\n".join(selected) + "\n[Lean: structured selection; other lines omitted]"
    elif policy.mode == "truncate":
        ids = TOKENIZER.encode(text, add_special_tokens=False).ids
        if len(ids) > policy.limit:
            marker = "\n[Lean: truncated; information lost]"
            keep = max(0, policy.limit - tokens(marker) - 2)
            text = TOKENIZER.decode(ids[:keep], skip_special_tokens=False) + marker
            while tokens(text) > policy.limit and keep:
                keep -= 1
                text = TOKENIZER.decode(ids[:keep], skip_special_tokens=False) + marker
    return {
        "text": text,
        "before_tokens": before,
        "after_tokens": tokens(text),
        "policy": asdict(policy),
        "changed": tokens(text) != before or policy.mode != "none",
    }


@dataclass(frozen=True)
class Tool:
    name: str
    version: str
    readonly: bool = False


class Middleware:
    """Run-local bounded TTL/LRU. Cache safety is an explicit caller contract."""

    def __init__(
        self,
        policy: Policy,
        scope: str,
        *,
        ttl: float = 10,
        capacity: int = 16,
        max_bytes: int = 1_000_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not scope or not math.isfinite(ttl) or ttl <= 0 or not 1 <= capacity <= 1000:
            raise ValueError("invalid cache bounds/scope")
        if not 1 <= max_bytes <= 10_000_000:
            raise ValueError("invalid byte capacity")
        self.policy, self.scope, self.clock = policy, scope, clock
        self.ttl, self.capacity, self.max_bytes = ttl, capacity, max_bytes
        self.entries: OrderedDict[str, tuple[float, str, int]] = OrderedDict()
        self.bytes = 0
        self.tool_invocations = 0
        self.cache_hits = 0

    def call(self, tool: Tool, args: Any, fn: Callable[[Any], str]) -> dict:
        wire = json.dumps(
            [self.scope, tool.name, tool.version, args],
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        if len(wire.encode()) > 65536:
            raise ValueError("arguments too large")
        key = hashlib.sha256(wire.encode()).hexdigest()
        now = self.clock()
        for expired in [k for k, (expiry, _, _) in self.entries.items() if expiry <= now]:
            _, _, size = self.entries.pop(expired)
            self.bytes -= size
        hit = self.policy.cache and tool.readonly and key in self.entries
        if hit:
            _, raw, _ = self.entries[key]
            self.entries.move_to_end(key)
            self.cache_hits += 1
        else:
            self.tool_invocations += 1
            raw = fn(copy.deepcopy(args))
            # Validate and transform before adding to cache. Failed/oversized results never cache.
            result = transform(raw, self.policy)
            size = len(raw.encode())
            if self.policy.cache and tool.readonly and size <= self.max_bytes:
                while self.entries and (
                    len(self.entries) >= self.capacity or self.bytes + size > self.max_bytes
                ):
                    _, (_, _, previous) = self.entries.popitem(last=False)
                    self.bytes -= previous
                self.entries[key] = (self.clock() + self.ttl, raw, size)
                self.bytes += size
            return {**result, "cache_hit": False}
        return {**transform(raw, self.policy), "cache_hit": True}


def cost(
    input_tokens: int,
    output_tokens: int,
    input_per_million: float | None = None,
    output_per_million: float | None = None,
) -> dict:
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
        raise ValueError("invalid usage")
    if input_per_million is None or output_per_million is None:
        return {"scenario_usd": None, "actual_usd": None, "basis": "not measured"}
    if any(not math.isfinite(v) or v < 0 for v in (input_per_million, output_per_million)):
        raise ValueError("invalid scenario rates")
    return {
        "scenario_usd": (input_tokens * input_per_million + output_tokens * output_per_million)
        / 1_000_000,
        "actual_usd": None,
        "basis": "user-supplied scenario; not an invoice",
    }


def complexity(source: str, previous: str = "") -> dict:
    """Signals, not a quality score. Only Python syntax/local lexical uses are inspected."""
    import difflib

    tree = ast.parse(source)
    imports = sorted(
        {
            name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for name in (
                [alias.name.split(".")[0] for alias in node.names]
                if isinstance(node, ast.Import)
                else [(node.module or "").split(".")[0]]
            )
        }
    )
    used = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    definitions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    old_imports = set()
    if previous:
        old = complexity(previous)
        old_imports = set(old["imports"])
    delta = list(difflib.ndiff(previous.splitlines(), source.splitlines()))
    return {
        "imports": imports,
        "added_imports": sorted(set(imports) - old_imports),
        "added_lines": sum(x.startswith("+ ") for x in delta),
        "removed_lines": sum(x.startswith("- ") for x in delta),
        "definitions_not_lexically_referenced": sorted(definitions - used),
        "limits": "signals only; exported entrypoints/dynamic references can be false positives",
    }
