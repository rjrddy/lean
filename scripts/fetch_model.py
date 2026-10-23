"""Public model, fixed revision; no token/account needed."""

from huggingface_hub import snapshot_download

snapshot_download(
    "HuggingFaceTB/SmolLM2-135M-Instruct",
    revision="12fd25f77366fa6b3b4b768ec3050bf629380bac",
    local_dir=".cache/model",
    allow_patterns=["*.json", "model.safetensors", "README.md"],
)
