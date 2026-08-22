from pathlib import Path

TRAINING_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TRAINING_ROOT.parent
API_ROOT = REPO_ROOT / "apps" / "api"
PROMPT_ROOT = API_ROOT / "app" / "prompts"


def safe_artifact_path(path: str | Path, *, base: Path = TRAINING_ROOT) -> Path:
    resolved = Path(path).expanduser().resolve()
    base_resolved = base.resolve()
    if resolved == base_resolved or base_resolved in resolved.parents:
        return resolved
    raise ValueError(f"Artifact path must stay under {base_resolved}: {resolved}")
