# GroundStack Training Pipeline

GroundStack includes an isolated supervised fine-tuning pipeline under `training/`.
It prepares canonical examples, validates provenance and safety constraints, produces
TRL-style conversational data, and can launch QLoRA adapter training on compatible
CUDA hardware.

The committed seed dataset is small fictional development data. It validates the
pipeline; it is not evidence of production fine-tuning quality.

## Workflow

```bash
make validate-training-data
make prepare-training-data
make training-preflight
make train-qlora CONFIG=training/configs/smoke_test.yaml
```

Use `training/configs/llama32_3b_qlora.yaml` for the real default configuration on a
CUDA host after accepting the Llama license and authenticating with Hugging Face.

## Governance

Only approved examples with known provenance, license, and redistribution rights can
enter a training dataset. GroundStack rejects secrets, obvious PII, unsafe URLs,
unknown-provenance data, unreviewed model output, and unlicensed scraped community
content.

Built with Llama. The default base model is configurable and defaults to
`meta-llama/Llama-3.2-3B-Instruct`; do not silently substitute a different model.

## Serving Paths

### PEFT/Transformers

Load the exact base model, then load the validated PEFT adapter. Validate tokenizer
and chat-template compatibility before smoke generation.

### vLLM

Run vLLM with LoRA support enabled, associate the adapter with its exact base model,
and expose it through GroundStack’s existing OpenAI-compatible provider by setting
`LLM_PROVIDER=openai_compatible` and the served model name.

### Ollama

Generate a Modelfile template:

```bash
PYTHONPATH=training python training/scripts/create_ollama_modelfile.py \
  --base llama3.2:3b \
  --adapter-path /absolute/path/to/validated/adapter
```

Then inspect it and create a local model:

```bash
ollama create groundstack-llama32-adapter -f training/reports/Modelfile.groundstack
ollama show groundstack-llama32-adapter
```

This documentation does not claim Ollama import succeeded unless those commands are
actually run. Adapter/base mismatches can produce incorrect behavior.
