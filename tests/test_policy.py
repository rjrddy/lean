from __future__ import annotations

import json
import random
import subprocess
from dataclasses import asdict

import pytest

from lean.policy import POLICIES, Middleware, Policy, Tool, complexity, cost, tokens, transform
from lean.tasks import tasks


def test_real_tokenizer_and_loss_markers():
    assert tokens("hello world") > 0
    assert transform("same\nsame\n", POLICIES[1])["text"].startswith("same\n[Lean: removed 1")
    assert transform("[INFO] junk\n[ASSERT] preserve", POLICIES[2])["text"].startswith(
        "[ASSERT] preserve"
    )
    assert transform("unknown format", POLICIES[2])["text"] == "unknown format"
    assert "information lost" in transform("hello world " * 500, POLICIES[4])["text"]


def test_truncation_budget_property():
    rng = random.Random(7301)
    for _ in range(120):
        text = " ".join(rng.choices(["hello", "x=1", "Straße", "中文", "🤖"], k=400))
        cap = rng.randrange(16, 200)
        result = transform(text, Policy("property", "truncate", cap))
        assert result["after_tokens"] <= cap
        assert result["before_tokens"] == tokens(text)


def test_readonly_cache_ttl_lru_versions_scopes_and_exceptions():
    clock = [0.0]
    middleware = Middleware(
        Policy("cache", cache=True), "tenant-and-run", ttl=1, capacity=2, clock=lambda: clock[0]
    )
    tool = Tool("read", "1", True)
    calls = []

    def fn(args):
        calls.append(args)
        return json.dumps(args)

    middleware.call(tool, {"a": 1, "b": 2}, fn)
    assert middleware.call(tool, {"b": 2, "a": 1}, fn)["cache_hit"]
    assert len(calls) == 1
    clock[0] = 2
    assert not middleware.call(tool, {"a": 1, "b": 2}, fn)["cache_hit"]
    assert not middleware.call(Tool("read", "2", True), {"a": 1, "b": 2}, fn)["cache_hit"]
    assert not middleware.call(Tool("read", "1", False), {"a": 1, "b": 2}, fn)["cache_hit"]
    middleware.call(tool, {"a": 3}, fn)
    middleware.call(tool, {"a": 4}, fn)
    assert not middleware.call(tool, {"a": 1, "b": 2}, fn)["cache_hit"]
    before = len(middleware.entries)
    with pytest.raises(RuntimeError):
        middleware.call(tool, {"fail": True}, lambda _: (_ for _ in ()).throw(RuntimeError()))
    assert len(middleware.entries) == before
    separate = Middleware(Policy("cache", cache=True), "another-run")
    assert not separate.call(tool, {"a": 1, "b": 2}, fn)["cache_hit"]


def test_cache_byte_bounds_and_bad_values():
    cache = Middleware(Policy("cache", cache=True), "bounded", max_bytes=10)
    for i in range(30):
        cache.call(Tool("r", "1", True), i, lambda _: "x" * 5)
        assert cache.bytes <= 10 and len(cache.entries) <= 2
    cache.call(Tool("r", "1", True), "big", lambda _: "x" * 20)
    assert cache.bytes <= 10
    with pytest.raises(ValueError):
        cache.call(Tool("r", "1", True), "oversize", lambda _: "x" * 65537)
    with pytest.raises(ValueError):
        Policy("bad", "unknown")
    with pytest.raises(ValueError):
        Middleware(Policy("bad"), "", ttl=0)


def test_no_invented_costs_and_complexity_signals():
    assert cost(100, 50)["actual_usd"] is None
    assert cost(1_000_000, 1_000_000, 2, 3)["scenario_usd"] == 5
    assert cost(1, 1, 2, 3)["actual_usd"] is None
    for rate in [float("nan"), float("inf"), -1]:
        with pytest.raises(ValueError):
            cost(1, 1, rate, 1)
    result = complexity("import json, math\nclass Factory: pass\ndef solve(): return 1")
    assert result["added_imports"] == ["json", "math"]
    assert "Factory" in result["definitions_not_lexically_referenced"]
    assert "false positives" in result["limits"]


def test_actual_fixture_patch_tests():
    for task in tasks():
        outcomes = []
        for candidate in task["candidates"]:
            result = subprocess.run(
                ["python3", "-I", "-c", candidate + "\n" + task["checks"]],
                capture_output=True,
                timeout=3,
            )
            outcomes.append(result.returncode == 0)
        assert sum(outcomes) == 1 and outcomes[task["correct_index"]]


def test_python_typescript_real_bpe_parity():
    fixtures = [
        {"text": text, "policy": asdict(policy)}
        for policy in POLICIES
        for text in [tasks()[0]["context"], "a\na\n", "Straße 中文 🤖 " * 80, "unknown format"]
    ]
    run = subprocess.run(
        ["apps/web/node_modules/.bin/tsx", "apps/web/src/sdk-test.ts"],
        input=json.dumps(fixtures),
        capture_output=True,
        text=True,
        check=True,
    )
    results = json.loads(run.stdout)
    for fixture, result in zip(fixtures, results, strict=True):
        assert transform(fixture["text"], Policy(**fixture["policy"])) == result


def test_actual_declared_dependency_delta():
    from lean.policy import dependency_delta

    result = dependency_delta(
        '{"dependencies":{"react":"1"}}',
        '{"dependencies":{"react":"2","lodash":"1"}}',
        "package.json",
    )
    assert result["added"] == ["lodash"] and result["changed"] == ["react"]
    result = dependency_delta(
        "[project]\ndependencies=[]", '[project]\ndependencies=["requests>=2"]', "pyproject.toml"
    )
    assert result["added"] == ["requests"]


def test_pluggable_filter_executes_for_live_and_cached_results():
    def plugin(text, policy):
        return transform(text.replace("noise", ""), policy)

    middleware = Middleware(Policy("plugin", cache=True), "plugin-run", filter_fn=plugin)
    tool = Tool("read", "1", True)
    assert middleware.call(tool, {}, lambda _: "noise signal")["text"] == " signal"
    assert middleware.call(tool, {}, lambda _: "not called")["text"] == " signal"
