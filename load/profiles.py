from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LoadProfile:
    name: str
    users: int
    spawn_rate: float
    run_time: str
    max_requests: int
    provider_mode: str
    dataset: str
    seed: int
    description: str
    safety: str
    requires_confirmation: bool = False
    warmup_seconds: int = 0

    def locust_args(self) -> list[str]:
        return [
            "--headless",
            "-u",
            str(self.users),
            "-r",
            str(self.spawn_rate),
            "--run-time",
            self.run_time,
        ]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PROFILES: dict[str, LoadProfile] = {
    "smoke": LoadProfile(
        name="smoke",
        users=1,
        spawn_rate=1,
        run_time="45s",
        max_requests=5,
        provider_mode="fake",
        dataset="load/datasets/questions_smoke.jsonl",
        seed=1201,
        description="One user, five deterministic questions, safe for CI.",
        safety="safe_by_default",
    ),
    "volume-300": LoadProfile(
        name="volume-300",
        users=3,
        spawn_rate=1,
        run_time="20m",
        max_requests=300,
        provider_mode="fake",
        dataset="load/datasets/questions_mixed.jsonl",
        seed=1202,
        description="Exactly 300 synthetic questions; not a user/adoption claim.",
        safety="moderate_local",
        requires_confirmation=True,
    ),
    "burst": LoadProfile(
        name="burst",
        users=8,
        spawn_rate=8,
        run_time="3m",
        max_requests=80,
        provider_mode="fake",
        dataset="load/datasets/questions_mixed.jsonl",
        seed=1203,
        description="Conservative community burst for queueing and rate limits.",
        safety="requires_stable_machine",
        requires_confirmation=True,
    ),
    "soak-short": LoadProfile(
        name="soak-short",
        users=4,
        spawn_rate=1,
        run_time="10m",
        max_requests=120,
        provider_mode="fake",
        dataset="load/datasets/questions_mixed.jsonl",
        seed=1204,
        description="Short sustained developer preset for leak and pool checks.",
        safety="requires_stable_machine",
        requires_confirmation=True,
    ),
    "soak-long": LoadProfile(
        name="soak-long",
        users=6,
        spawn_rate=1,
        run_time="60m",
        max_requests=1000,
        provider_mode="fake",
        dataset="load/datasets/questions_mixed.jsonl",
        seed=1205,
        description="Optional long sustained traffic profile.",
        safety="manual_only",
        requires_confirmation=True,
        warmup_seconds=60,
    ),
    "spike-recovery": LoadProfile(
        name="spike-recovery",
        users=12,
        spawn_rate=12,
        run_time="5m",
        max_requests=150,
        provider_mode="fake",
        dataset="load/datasets/questions_mixed.jsonl",
        seed=1206,
        description="Rapid increase followed by recovery observation.",
        safety="manual_only",
        requires_confirmation=True,
    ),
    "mixed-discord": LoadProfile(
        name="mixed-discord",
        users=4,
        spawn_rate=1,
        run_time="5m",
        max_requests=100,
        provider_mode="fake",
        dataset="load/datasets/questions_mixed.jsonl",
        seed=1207,
        description="Web chat, retrieval, Discord PING simulation, feedback, and status checks.",
        safety="requires_stable_machine",
        requires_confirmation=True,
    ),
    "ollama": LoadProfile(
        name="ollama",
        users=1,
        spawn_rate=1,
        run_time="5m",
        max_requests=20,
        provider_mode="ollama",
        dataset="load/datasets/questions_smoke.jsonl",
        seed=1208,
        description="Local Ollama sample, kept separate from mock capacity.",
        safety="manual_only_single_model",
        requires_confirmation=True,
    ),
    "real-provider": LoadProfile(
        name="real-provider",
        users=1,
        spawn_rate=1,
        run_time="3m",
        max_requests=10,
        provider_mode="hosted",
        dataset="load/datasets/questions_smoke.jsonl",
        seed=1209,
        description="Opt-in hosted provider sample with strict request ceiling.",
        safety="paid_or_quota_sensitive",
        requires_confirmation=True,
    ),
}


def profile(name: str) -> LoadProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown load profile: {name}") from exc
