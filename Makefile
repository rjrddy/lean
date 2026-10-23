PY = .venv/bin/python
.PHONY: setup build lint test bench demo models eval
setup:
	python3 -m venv .venv
	$(PY) -m pip install -e . -r requirements-dev.txt
	npm --prefix apps/web ci
build:
	npm --prefix apps/web run build
lint:
	.venv/bin/ruff check src tests scripts
	.venv/bin/ruff format --check src tests scripts
	npm --prefix apps/web run lint
test:
	$(PY) -m pytest -q
bench:
	$(PY) scripts/bench.py
models:
	$(PY) -m pip install -e '.[model]'
	$(PY) scripts/fetch_model.py
eval:
	$(PY) scripts/evaluate.py
demo: setup build
	$(PY) -m lean.server
