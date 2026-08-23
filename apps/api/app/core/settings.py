from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GroundStack"
    app_env: str = Field(default="development")
    environment: str = "local"
    log_level: str = "INFO"
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://groundstack:groundstack@localhost:5432/groundstack"
    )
    database_direct_url: str = ""
    db_ssl_required: bool = False
    db_pool_size: int = Field(default=5, ge=1, le=20)
    redis_url: str = ""
    redis_timeout_seconds: float = Field(default=1.5, gt=0, le=10)
    redis_key_namespace: str = "groundstack"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    public_api_base_url: str = "http://localhost:8000"
    embedding_provider: str = "sentence_transformers"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    embedding_batch_size: int = 16
    embedding_device: str = "auto"
    chunk_target_tokens: int = 350
    chunk_overlap_tokens: int = 60
    max_ingestion_file_size_bytes: int = 10 * 1024 * 1024
    url_ingestion_allowed_domains: list[str] = []
    max_retrieval_query_length: int = 1200
    vector_candidate_limit: int = 40
    lexical_candidate_limit: int = 40
    rrf_k: int = 60
    vector_rrf_weight: float = 1.0
    lexical_rrf_weight: float = 1.0
    rerank_candidate_limit: int = 20
    retrieval_final_top_k: int = 8
    retrieval_max_top_k: int = 20
    max_chunks_per_source: int = 3
    retrieval_algorithm_version: str = "hybrid-rrf-ce-v1"
    reranker_provider: str = "sentence_transformers"
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    reranker_batch_size: int = 16
    reranker_device: str = "auto"
    reranking_enabled: bool = True
    persist_retrieval_queries: bool = False
    retrieval_debug_enabled: bool = True
    retrieval_timeout_seconds: float = 30.0
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_api_key: str = ""
    llm_timeout_seconds: float | None = Field(default=None, gt=0)
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    llm_max_output_tokens: int = Field(default=700, ge=1, le=4096)
    llm_context_window: int = Field(default=8192, ge=1024)
    llm_request_timeout_seconds: float = Field(default=120.0, gt=0)
    llm_prewarm: bool = False
    llm_max_retries: int = Field(default=1, ge=0, le=3)
    fake_llm_first_token_delay_ms: int = Field(default=25, ge=0, le=10000)
    fake_llm_token_rate_per_second: float = Field(default=80.0, gt=0, le=1000)
    fake_llm_total_tokens: int = Field(default=80, ge=1, le=4096)
    fake_llm_failure_mode: str = Field(default="none")
    llm_max_concurrent_requests: int | None = Field(default=None, ge=1, le=32)
    llm_model_variant: str = "base"
    llm_adapter_name: str = ""
    llm_adapter_version: str = ""
    llm_dataset_version: str = ""
    llm_model_manifest_checksum: str = ""
    llm_evaluation_status: str = "not_evaluated"
    llm_promotion_status: str = "created"
    tokenizer_model_name: str = ""
    store_generation_prompts: bool = False
    generation_prompt_version: str = "grounded_answer/v1"
    max_conversation_history_messages: int = Field(default=8, ge=0, le=30)
    feedback_rate_limit_per_minute: int = Field(default=30, ge=1, le=600)
    chat_rate_limit_per_minute: int = Field(default=20, ge=1, le=300)
    retrieval_rate_limit_per_minute: int = Field(default=60, ge=1, le=600)
    generation_concurrency: int = Field(default=2, ge=1, le=32)
    retrieval_concurrency: int = Field(default=4, ge=1, le=64)
    model_queue_timeout_seconds: float = Field(default=3.0, ge=0.05, le=60.0)
    metrics_enabled: bool = True
    metrics_internal_token: str = ""
    evaluation_admin_enabled: bool = False
    otel_tracing_enabled: bool = False
    otlp_endpoint: str = ""
    oidc_issuer_url: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_audience: str = ""
    oidc_scopes: str = "openid profile email"
    oidc_role_claim: str = "roles"
    oidc_admin_role: str = "admin"
    oidc_allowed_algorithms: list[str] = ["RS256"]
    session_cookie_name: str = "groundstack_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    session_lifetime_seconds: int = Field(default=3600, ge=300, le=86400)
    allow_anonymous_demo: bool = False
    demo_chat_enabled: bool = True
    demo_allowlist_mode: bool = False
    demo_allowlist_ips: list[str] = []
    demo_request_limit_per_minute: int = Field(default=8, ge=1, le=60)
    demo_daily_question_limit: int = Field(default=100, ge=1, le=10000)
    demo_daily_token_limit: int = Field(default=15000, ge=1000, le=100000)
    demo_max_question_length: int = Field(default=600, ge=20, le=2000)
    demo_max_context_tokens: int = Field(default=2500, ge=500, le=12000)
    demo_provider_failure_threshold: int = Field(default=5, ge=1, le=100)
    demo_provider_failure_window_seconds: int = Field(default=300, ge=30, le=3600)
    demo_redis_required: bool = False
    demo_upload_limit_bytes: int = Field(default=0, ge=0)
    demo_max_conversations: int = Field(default=5, ge=1, le=50)
    discord_integration_enabled: bool = False
    discord_application_id: str = ""
    discord_public_key: str = ""
    discord_bot_token: str = ""
    discord_interaction_token_encryption_key: str = ""
    discord_identity_hmac_key: str = ""
    discord_signature_tolerance_seconds: int = Field(default=300, ge=30, le=900)
    discord_default_retention_days: int = Field(default=30, ge=1, le=365)
    discord_max_question_length: int = Field(default=600, ge=20, le=2000)
    discord_queue_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    discord_worker_batch_size: int = Field(default=5, ge=1, le=25)
    discord_worker_max_retries: int = Field(default=2, ge=0, le=5)
    discord_response_base_url: str = "https://discord.com/api/v10"
    discord_full_answer_base_url: str = ""
    discord_allow_dms: bool = False
    dev_auth_bypass_enabled: bool = True
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver", "test"]
    trusted_proxy_hosts: list[str] = []
    csrf_cookie_name: str = "groundstack_csrf"
    csrf_header_name: str = "x-groundstack-csrf"
    docs_enabled: bool = True
    max_request_body_bytes: int = Field(default=12 * 1024 * 1024, ge=1024)

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("url_ingestion_allowed_domains", mode="before")
    @classmethod
    def parse_allowed_domains(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [domain.strip().lower() for domain in value.split(",") if domain.strip()]
        return [domain.lower() for domain in value]

    @field_validator(
        "trusted_hosts",
        "trusted_proxy_hosts",
        "oidc_allowed_algorithms",
        "demo_allowlist_ips",
        mode="before",
    )
    @classmethod
    def parse_string_lists(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_runtime_mode(self) -> "Settings":
        valid_envs = {"development", "demo", "production", "test"}
        if self.app_env not in valid_envs:
            raise ValueError(f"APP_ENV must be one of {sorted(valid_envs)}.")
        if self.app_env == "production":
            missing = [
                name
                for name, value in {
                    "OIDC_ISSUER_URL": self.oidc_issuer_url,
                    "OIDC_CLIENT_ID": self.oidc_client_id,
                    "OIDC_AUDIENCE": self.oidc_audience,
                    "METRICS_INTERNAL_TOKEN": self.metrics_internal_token,
                }.items()
                if not value
            ]
            if missing:
                raise ValueError(
                    "Production configuration is incomplete: "
                    + ", ".join(missing)
                    + " must be set."
                )
            if self.dev_auth_bypass_enabled:
                raise ValueError("DEV_AUTH_BYPASS_ENABLED cannot be true in production.")
            if "*" in self.cors_origins or not self.cors_origins:
                raise ValueError("Production CORS origins must be exact and non-empty.")
            if not self.trusted_hosts or "*" in self.trusted_hosts:
                raise ValueError("Production TRUSTED_HOSTS must be exact and non-empty.")
            if not self.session_cookie_secure:
                raise ValueError("Production sessions require secure cookies.")
        if (
            self.app_env == "demo"
            and self.allow_anonymous_demo
            and self.demo_upload_limit_bytes != 0
        ):
            raise ValueError("Anonymous demo upload limit must remain 0; uploads are admin-only.")
        if self.app_env == "demo" and self.dev_auth_bypass_enabled:
            raise ValueError("DEV_AUTH_BYPASS_ENABLED cannot be true in demo.")
        if self.app_env == "demo" and self.docs_enabled:
            raise ValueError("DOCS_ENABLED must be false in public demo mode.")
        if self.app_env == "demo" and self.llm_provider == "openai_compatible":
            if not self.llm_base_url or not self.llm_api_key or not self.llm_model:
                raise ValueError(
                    "Demo OpenAI-compatible inference requires LLM_BASE_URL, "
                    "LLM_API_KEY, and LLM_MODEL."
                )
        if self.discord_integration_enabled:
            missing_discord = [
                name
                for name, value in {
                    "DISCORD_APPLICATION_ID": self.discord_application_id,
                    "DISCORD_PUBLIC_KEY": self.discord_public_key,
                    "DISCORD_BOT_TOKEN": self.discord_bot_token,
                    "DISCORD_INTERACTION_TOKEN_ENCRYPTION_KEY": (
                        self.discord_interaction_token_encryption_key
                    ),
                    "DISCORD_IDENTITY_HMAC_KEY": self.discord_identity_hmac_key,
                }.items()
                if not value
            ]
            if missing_discord:
                raise ValueError(
                    "Discord integration is enabled but missing: " + ", ".join(missing_discord)
                )
        if self.app_env == "test" and self.llm_provider not in {"fake", "ollama"}:
            raise ValueError(
                "Test mode cannot use remote model providers unless explicitly overridden."
            )
        fake_modes = {
            "none",
            "timeout",
            "http_429",
            "http_500",
            "connection_failure",
            "malformed",
            "stream_interruption",
        }
        if self.fake_llm_failure_mode not in fake_modes:
            raise ValueError(f"FAKE_LLM_FAILURE_MODE must be one of {sorted(fake_modes)}.")
        return self

    @property
    def effective_llm_timeout_seconds(self) -> float:
        return self.llm_timeout_seconds or self.llm_request_timeout_seconds

    @property
    def effective_generation_concurrency(self) -> int:
        return self.llm_max_concurrent_requests or self.generation_concurrency


@lru_cache
def get_settings() -> Settings:
    return Settings()
