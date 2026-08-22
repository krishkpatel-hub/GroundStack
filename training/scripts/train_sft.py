from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from groundstack_training.config import dump_resolved_config, load_yaml, validate_config
from groundstack_training.dataset import prepare_dataset
from groundstack_training.lora import parameter_counts, validate_lora_targets, verify_base_frozen
from groundstack_training.preflight import hardware_preflight


def _tiny_smoke(output_dir: Path, config: dict[str, object]) -> dict[str, object]:
    fake_modules = ["model.layers.0.self_attn.q_proj", "model.layers.0.mlp.down_proj"]
    targets = validate_lora_targets(fake_modules, ["q_proj", "down_proj"])
    params = [
        ("base.model.layers.0.self_attn.q_proj.weight", 1000, False),
        ("base.model.layers.0.mlp.down_proj.weight", 1000, False),
        ("base.lora_A.default.weight", 64, True),
        ("base.lora_B.default.weight", 64, True),
    ]
    counts = parameter_counts(params)
    if not verify_base_frozen(params):
        raise RuntimeError("Smoke model has unfrozen base parameters.")
    adapter = output_dir / "adapter"
    adapter.mkdir(parents=True, exist_ok=True)
    (adapter / "adapter_config.json").write_text(
        json.dumps({"r": 2, "target_modules": targets, "base_model_name_or_path": "tiny-smoke"}),
        encoding="utf-8",
    )
    (adapter / "adapter_model.safetensors").write_text("tiny-smoke-placeholder", encoding="utf-8")
    return {"mode": "tiny_smoke", "target_modules": targets, **counts}


def _run_qlora(output_dir: Path, config: dict[str, object]) -> dict[str, object]:
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    base_model = str(config["base_model"])
    qlora = dict(config["qlora"])
    lora = dict(config["lora"])
    training = dict(config["training"])
    dataset_dir = output_dir / "dataset"
    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=qlora["bnb_4bit_quant_type"],
        bnb_4bit_use_double_quant=bool(qlora["bnb_4bit_use_double_quant"]),
        bnb_4bit_compute_dtype=compute_dtype,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    if tokenizer.chat_template is None:
        raise RuntimeError("Base tokenizer has no chat template; refusing to train.")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=quantization,
        device_map="auto",
        torch_dtype=compute_dtype,
    )
    model.config.use_cache = False
    if bool(qlora.get("gradient_checkpointing", True)):
        model.gradient_checkpointing_enable()
    module_names = [name for name, _ in model.named_modules()]
    target_modules = validate_lora_targets(module_names, str(lora["target_modules"]))
    model = prepare_model_for_kbit_training(model)
    peft_config = LoraConfig(
        r=int(lora["rank"]),
        lora_alpha=int(lora["alpha"]),
        lora_dropout=float(lora["dropout"]),
        target_modules=target_modules,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    params = [
        (name, parameter.numel(), parameter.requires_grad)
        for name, parameter in model.named_parameters()
    ]
    counts = parameter_counts(params)
    if not verify_base_frozen(params):
        raise RuntimeError("Base parameters are trainable after applying LoRA; refusing to train.")

    data_files = {
        "train": str(dataset_dir / "train.jsonl"),
        "validation": str(dataset_dir / "validation.jsonl"),
    }
    datasets = load_dataset("json", data_files=data_files)

    def formatting_func(example: dict[str, object]) -> str:
        return tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )

    args = SFTConfig(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=float(training["epochs"]),
        per_device_train_batch_size=int(training["per_device_train_batch_size"]),
        gradient_accumulation_steps=int(training["gradient_accumulation_steps"]),
        learning_rate=float(training["learning_rate"]),
        warmup_ratio=float(training["warmup_ratio"]),
        lr_scheduler_type=str(training["scheduler"]),
        weight_decay=float(training["weight_decay"]),
        max_grad_norm=float(training["gradient_clipping"]),
        max_length=int(training["max_sequence_length"]),
        completion_only_loss=bool(training["completion_only_loss"]),
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="epoch",
        seed=int(training["seed"]),
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        formatting_func=formatting_func,
        processing_class=tokenizer,
    )
    trainer.train()
    metrics = trainer.evaluate()
    adapter_dir = output_dir / "adapter"
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    return {
        "mode": "cuda_qlora",
        "target_modules": target_modules,
        "metrics": metrics,
        **counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GroundStack SFT/QLoRA training.")
    parser.add_argument("--config", default="training/configs/smoke_test.yaml")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tiny-smoke", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    config = load_yaml(args.config)
    errors = validate_config(config)
    if errors:
        raise SystemExit("\n".join(errors))
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir or f"training/reports/runs/{run_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    dump_resolved_config(output_dir / "resolved_config.json", config)
    preflight = hardware_preflight(
        base_model=str(config["base_model"]), output_path=output_dir / "hardware_report.json"
    )
    dataset_config = dict(config["dataset"])
    split = dict(config.get("split", {}))
    dataset_manifest = prepare_dataset(
        source_path=dataset_config["source_path"],
        output_dir=output_dir / "dataset",
        dataset_name=dataset_config["name"],
        version=str(dataset_config["version"]),
        seed=int(split.get("seed", 42)),
        train_ratio=float(split.get("train_ratio", 0.7)),
        validation_ratio=float(split.get("validation_ratio", 0.15)),
        near_duplicate_threshold=float(dataset_config.get("near_duplicate_threshold", 0.94)),
        prompt_version=str(config.get("prompt_version", "grounded_answer/v1")),
    )
    if args.dry_run:
        training_result = {
            "mode": "dry_run",
            "message": "Validated config, preflight, and dataset.",
        }
    elif args.tiny_smoke or config.get("smoke_test"):
        training_result = _tiny_smoke(output_dir, config)
    else:
        if preflight["estimated_training_compatibility"] != "cuda_qlora_ready":
            raise SystemExit("CUDA QLoRA is not available. Run with --dry-run or use a CUDA GPU.")
        try:
            import bitsandbytes  # noqa: F401
            import datasets  # noqa: F401
            import peft  # noqa: F401
            import torch  # noqa: F401
            import transformers  # noqa: F401
            import trl  # noqa: F401
        except ModuleNotFoundError as exc:
            raise SystemExit(f"Missing training dependency: {exc.name}") from exc
        training_result = _run_qlora(output_dir, config)
    manifest = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "base_model": config["base_model"],
        "dataset_manifest": dataset_manifest,
        "hardware_report": preflight,
        "training_result": training_result,
        "duration_seconds": round(time.perf_counter() - started, 3),
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
