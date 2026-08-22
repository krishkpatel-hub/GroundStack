from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


class DemoAvailabilityResponse(BaseModel):
    state: str
    chat_enabled: bool
    reason: str
    retry_after_seconds: int | None = None


class DatabaseStatus(BaseModel):
    connected: bool
    detail: str


class KnowledgeCounts(BaseModel):
    knowledge_sources: int
    document_versions: int
    chunks: int
    completed_ingestion_jobs: int
    failed_ingestion_jobs: int


class EmbeddingStatus(BaseModel):
    provider: str
    model: str
    dimension: int
    device: str
    loaded: bool = False


class RerankerStatus(BaseModel):
    provider: str
    model: str
    device: str
    enabled: bool
    loaded: bool = False


class RetrievalStatus(BaseModel):
    algorithm_version: str
    reranking_enabled: bool
    vector_index_available: bool
    text_search_index_available: bool
    searchable_sources: int
    searchable_chunks: int


class LLMStatus(BaseModel):
    provider: str
    model: str
    reachable: bool
    model_available: bool
    loaded: bool | None = None
    detail: str
    model_variant: str = "base"
    adapter_name: str | None = None
    adapter_version: str | None = None
    dataset_version: str | None = None
    model_manifest_checksum: str | None = None
    evaluation_status: str = "not_evaluated"
    promotion_status: str = "created"


class SystemStatusResponse(BaseModel):
    application: str
    environment: str
    database: DatabaseStatus
    embeddings: EmbeddingStatus
    reranker: RerankerStatus
    retrieval: RetrievalStatus
    llm: LLMStatus
    knowledge: KnowledgeCounts

    model_config = ConfigDict(json_schema_extra={"examples": [{"application": "online"}]})
