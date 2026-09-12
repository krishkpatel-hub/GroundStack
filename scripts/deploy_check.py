from __future__ import annotations

import os
from urllib.parse import urlparse

REQUIRED_DEMO_VARS = [
    "APP_ENV",
    "DATABASE_URL",
    "LLM_PROVIDER",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "NEXT_PUBLIC_API_BASE_URL",
]


def _host(value: str) -> str:
    parsed = urlparse(value)
    return parsed.hostname or "unset"


def main() -> int:
    missing = [name for name in REQUIRED_DEMO_VARS if not os.getenv(name)]
    app_env = os.getenv("APP_ENV", "")
    errors: list[str] = []
    if app_env != "demo":
        errors.append("APP_ENV must be demo for public launch checks.")
    if os.getenv("DEV_AUTH_BYPASS_ENABLED", "").lower() == "true":
        errors.append("DEV_AUTH_BYPASS_ENABLED must be false.")
    if os.getenv("DOCS_ENABLED", "").lower() == "true":
        errors.append("DOCS_ENABLED must be false for the public demo.")
    if os.getenv("DEMO_CHAT_ENABLED", "true").lower() != "true":
        errors.append("DEMO_CHAT_ENABLED is off; launch would be in maintenance mode.")
    if os.getenv("LLM_PROVIDER") == "openai_compatible" and not os.getenv("LLM_API_KEY"):
        errors.append("OpenAI-compatible hosted inference requires LLM_API_KEY.")
    if missing:
        errors.append("Missing required variables: " + ", ".join(sorted(missing)))

    print("GroundStack deploy check")
    print(f"database_host={_host(os.getenv('DATABASE_URL', ''))}")
    print(f"llm_provider={os.getenv('LLM_PROVIDER', 'unset')}")
    print(f"llm_model={os.getenv('LLM_MODEL', 'unset')}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Deploy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
