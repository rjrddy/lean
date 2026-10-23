# Run and demonstrate

Prerequisites: Python and Node/npm. From a fresh clone, `make demo` installs the lightweight dependencies, builds React, and serves http://127.0.0.1:8092. The public tokenizer is vendored; the default demo downloads no weights and uses no account. Model charts are retained actual inference evidence, labelled separately from the live filter/cache lab. Ctrl-C stops the server. Set PORT to override the HTTP port. No persistent user database exists.

For a fresh real inference run, `make models eval` installs the optional model runtime and fetches the pinned public weights. It overwrites evaluation.json only when the complete run finishes. Preserve the existing evidence if comparing experiments. `make bench` runs middleware measurements, semantic-loss controls, archive token recount and the expected rejecting promotion gate; it does not run model inference. Source-fix before/after model results are both retained under docs/results/.

## Record a ninety-second walkthrough

Start recording before the following actions; explain the scope while interacting rather than padding idle footage:

- Read the model-validity warning. Select baseline and the other policies; compare input tokens and the observed pass count on the full chart/table.
- Enter your own assumed input-token price. Explain that this is a scenario excluding output/infrastructure, not an invoice. Clear the input.
- Change candidate-order seed. Select a failed task, inspect its actual chosen patch and test assertion failure. Show a passing task too.
- Open the live policy lab, apply summary, and compare the raw synthetic output with its real filtered tokens and retained source block.
- Select balanced and show the live read-only cache hit. Explain that repeated context still costs prompt tokens and the demo cache lasts only for this request.
- Apply truncation, inspect the missing final assertion, and open the recorded loss controls. End with the low-competence model and unmeasured-dollar limitations.

Automated recorder: install requirements-browser.txt, run `.venv/bin/python -m playwright install chromium ffmpeg`, then `.venv/bin/python scripts/review.py --record`. It launches/stops its own server and performs repeated real filter/cache interactions. `PLAYWRIGHT_BROWSERS_PATH` can point to a compatible existing cache. Video: docs/results/browser/demo.webm. Check actual duration with `ffprobe -v quiet -show_format -of json docs/results/browser/demo.webm`; there is no padded idle clip.

## Deployment preparation

Dockerfile and Render free-plan blueprint are prepared only. No account was created and nothing was deployed. A future approved deployment generates LEAN_TOKEN; enter it in the UI's in-memory Connection settings. The image serves retained model results and live filtering, not hosted model inference. Free-plan instances may sleep/restart; no hosted latency or availability is measured. Review TLS, identity and abuse controls before sharing it beyond a single-user developer tool.
