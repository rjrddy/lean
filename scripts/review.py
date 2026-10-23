"""Review the actual report UI and live compression/cache endpoint; optional real recording."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/results/browser"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    receipts = []
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "server.log"
        with path.open("w") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "lean.server"],
                env={**os.environ, "PORT": "0"},
                stdout=log,
                stderr=log,
            )
            try:
                base = ""
                for _ in range(200):
                    for line in path.read_text().splitlines():
                        row = json.loads(line)
                        if row.get("event") == "ready":
                            base = row["url"]
                    if base:
                        break
                    if process.poll() is not None:
                        raise RuntimeError(path.read_text())
                    time.sleep(0.025)
                assert base
                with sync_playwright() as p:
                    browser = p.chromium.launch(executable_path=p.chromium.executable_path)
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 1000},
                        **(
                            {
                                "record_video_dir": temp,
                                "record_video_size": {"width": 1440, "height": 1000},
                            }
                            if args.record
                            else {}
                        ),
                    )
                    page = context.new_page()
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(base)
                    expect(page.get_by_role("heading", level=1)).to_contain_text("Cut the noise")
                    expect(page.locator(".validity")).to_contain_text("weak result")
                    started = time.monotonic()

                    def exercise(index: int):
                        policy = ["baseline", "dedupe", "summary", "trim256", "trim64", "balanced"][
                            index % 6
                        ]
                        page.locator(".policies button").nth(index % 6).click()
                        page.locator(".task-list button").nth(index % 8).click()
                        with page.expect_response("**/api/lab") as response:
                            page.get_by_role("button", name=f"Apply {policy} →", exact=True).click()
                        row = response.value.json()
                        expect(page.locator(".lab-receipt")).to_contain_text(
                            f"{row['first']['before_tokens']} → "
                            f"{row['first']['after_tokens']} tokens"
                        )
                        assert row["cache_hits"] == (1 if policy == "balanced" else 0)
                        assert not row.get("inference_run", True)
                        receipts.append(
                            {
                                "policy": policy,
                                "before_tokens": row["first"]["before_tokens"],
                                "after_tokens": row["first"]["after_tokens"],
                                "tool_invocations": row["invocations"],
                                "cache_hits": row["cache_hits"],
                            }
                        )

                    for i in range(6):
                        exercise(i)
                    page.get_by_label("Scenario input rate").fill("2")
                    expect(page.locator("tbody")).to_contain_text("0.049194")
                    page.get_by_label("Scenario input rate").fill("")
                    page.get_by_label("Candidate-order seed").select_option("7302")
                    page.locator(".policies button").nth(2).click()
                    exercise(2)
                    page.screenshot(path=str(OUT / "desktop.png"), full_page=True)
                    widths = []
                    for width in [390, 768, 1024, 1440]:
                        page.set_viewport_size({"width": width, "height": 1000})
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                        widths.append(width)
                    page.set_viewport_size({"width": 390, "height": 1000})
                    page.screenshot(path=str(OUT / "mobile.png"), full_page=True)
                    page.set_viewport_size({"width": 1440, "height": 1000})
                    page.route("**/api/lab", lambda route: route.abort())
                    page.get_by_role("button", name="Apply summary →", exact=True).click()
                    expect(page.get_by_role("alert")).to_be_visible()
                    page.unroute("**/api/lab")
                    exercise(5)
                    expect(page.get_by_role("alert")).to_have_count(0)
                    page.keyboard.press("Tab")
                    assert page.evaluate("document.activeElement !== document.body")
                    i = 6
                    if args.record:
                        while time.monotonic() - started < 92:
                            exercise(i)
                            i += 1
                    video = page.video
                    context.close()
                    if video:
                        video.save_as(str(OUT / "demo.webm"))
                    browser.close()
                    assert not errors, errors
                    result = {
                        "responsive_widths": widths,
                        "page_errors": errors,
                        "network_failure_recovery": True,
                        "keyboard_focus": True,
                        "live_filter_receipts": receipts,
                        "elapsed_s": time.monotonic() - started,
                        "model_basis": "retained actual model evaluation, not live inference",
                    }
                    if args.record:
                        result["ffprobe"] = json.loads(
                            subprocess.check_output(
                                [
                                    "ffprobe",
                                    "-v",
                                    "quiet",
                                    "-show_format",
                                    "-of",
                                    "json",
                                    str(OUT / "demo.webm"),
                                ],
                                text=True,
                            )
                        )
                        assert float(result["ffprobe"]["format"]["duration"]) >= 90
                    (OUT / "review.json").write_text(json.dumps(result, indent=2) + "\n")
                    print(
                        json.dumps({k: v for k, v in result.items() if k != "live_filter_receipts"})
                    )
            finally:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
