# Lean provenance

The approved salvage audit selected no direct old source transfer for Lean. This repository's middleware, Python/TypeScript SDKs, cache, synthetic coding fixtures, paired inference runner, report, tests and UI were written here.

Public assets only: SmolLM model/tokenizer at the pinned revision recorded in evaluation.json and assets/README.md. Existing ignored local public-model files were copied read-only into this repository's ignored model cache to avoid downloading identical weights. The first actual evaluation used the already installed model runtime in Pulse's virtualenv without modifying it; the recorded environment names versions and hashes. `make models eval` installs an independent runtime for fresh reproduction. No Pulse source or interface was copied or changed.

No Stepwise integration is active. Both sides must independently pass before traces feed this project. No old directory or remote was deleted, no employer data/code was used, and no hosted account was created.
