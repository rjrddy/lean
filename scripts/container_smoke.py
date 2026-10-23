"""Smoke actual image, static assets, auth and live tokenizer/cache requests."""

from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:18092"
TOKEN = "synthetic-ci-console-key-0001"


def request(path: str, data=None):
    req = urllib.request.Request(
        BASE + path,
        data=None if data is None else json.dumps(data).encode(),
        headers={"Authorization": "Bearer " + TOKEN},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


def main() -> None:
    name = "lean-ci-smoke"
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-p",
            "127.0.0.1:18092:8092",
            "-e",
            "LEAN_TOKEN=" + TOKEN,
            "lean:test",
        ],
        check=True,
    )
    try:
        for _ in range(60):
            try:
                if request("/api/health")["status"] == "ready":
                    break
            except (OSError, urllib.error.HTTPError):
                time.sleep(0.5)
        else:
            raise AssertionError("not ready")
        uid = subprocess.check_output(["docker", "exec", name, "id", "-u"], text=True).strip()
        assert uid == "10001"
        with urllib.request.urlopen(BASE) as response:
            html = response.read().decode()
        assert "Lean" in html
        asset = re.search(r'src="([^"]+\.js)"', html).group(1)
        with urllib.request.urlopen(BASE + asset) as response:
            assert response.status == 200 and len(response.read()) > 0
        with_error = False
        try:
            urllib.request.urlopen(BASE + "/api/report")
        except urllib.error.HTTPError as error:
            with_error = error.code == 401
        assert with_error
        before = request("/api/report")
        row = request("/api/lab", {"policy": "balanced", "task": "empty-mean"})
        assert row["cache_hits"] == 1 and row["invocations"] == 1
        assert row["first"]["after_tokens"] < row["first"]["before_tokens"]
        subprocess.run(["docker", "restart", name], check=True)
        for _ in range(60):
            try:
                assert request("/api/report") == before
                break
            except (OSError, urllib.error.HTTPError):
                time.sleep(0.5)
        else:
            raise AssertionError("restart failed")
        print(
            json.dumps(
                {
                    "image": "pass",
                    "uid": uid,
                    "static_asset": True,
                    "auth": True,
                    "live_cache_hits": row["cache_hits"],
                    "recorded_report_restart_equal": True,
                }
            )
        )
    finally:
        subprocess.run(["docker", "logs", name], check=True)
        subprocess.run(["docker", "rm", "-f", name], check=True)


if __name__ == "__main__":
    main()
