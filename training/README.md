# GroundStack Training

This directory contains the reproducible dataset and adapter-training pipeline for
GroundStack Prompt 6. It is intentionally isolated from the production API.

The committed seed dataset is fictional, project-original development data. It is
for validating the pipeline and smoke tests only; it is not a production-scale
fine-tuning dataset.

## Setup

```bash
cd training
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Install QLoRA dependencies only on a suitable training host:

```bash
pip install -e ".[qlora]"
```

The default base model is `meta-llama/Llama-3.2-3B-Instruct`. You must accept the
applicable Llama license and authenticate with Hugging Face through normal secure
tooling such as `huggingface-cli login`. Do not paste access tokens into source code
or notebooks.

Built with Llama. See the Llama license reference in
`training/data/manifests/provenance_manifest.json`.

## Commands

From the repository root:

```bash
make validate-training-data
make prepare-training-data
make training-preflight
make train-qlora CONFIG=training/configs/smoke_test.yaml
make compare-models BASE_MODEL=meta-llama/Llama-3.2-3B-Instruct ADAPTER_PATH=path/to/adapter
```

`make train-qlora` runs the same `training/scripts/train_sft.py` entrypoint used by
the Colab notebook. On macOS or CPU-only machines it validates config, dataset, and
hardware readiness but does not claim a CUDA QLoRA run completed.

## Real QLoRA Runs

Run real training only on compatible CUDA hardware with enough VRAM, disk, and access
to the exact configured base model. The training script validates:

- configuration
- prompt checksum
- dataset manifest and checksum
- CUDA preflight
- LoRA target module selection
- frozen base parameters
- run manifest creation

Adapter artifacts and checkpoints are written under `training/reports/runs/` and are
ignored by git.

## Serving

Serving instructions are documented in `docs/training.md` for PEFT/Transformers,
vLLM LoRA serving, and Ollama Modelfile generation. Adapter/base mismatches can
produce incorrect behavior; never present an adapter as usable until compatibility
has been validated.
