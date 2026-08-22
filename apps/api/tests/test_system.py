from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.system import DatabaseStatus
from app.services.ai.types import LLMHealth


async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "GroundStack"}


async def test_system_status_endpoint(monkeypatch) -> None:
    async def healthy_database() -> DatabaseStatus:
        return DatabaseStatus(connected=True, detail="ok")

    async def empty_counts(_self) -> dict[str, int]:
        return {
            "knowledge_sources": 0,
            "document_versions": 0,
            "chunks": 0,
            "completed_ingestion_jobs": 0,
            "failed_ingestion_jobs": 0,
        }

    async def index_status(_self) -> dict[str, bool]:
        return {"hnsw": True, "gin": True}

    async def searchable_counts(_self) -> dict[str, int]:
        return {"searchable_sources": 0, "searchable_chunks": 0}

    class FakeLLMProvider:
        async def health(self) -> LLMHealth:
            return LLMHealth(
                provider="ollama",
                model="llama3.2:3b",
                reachable=True,
                model_available=True,
                loaded=True,
                detail="ready",
            )

    monkeypatch.setattr("app.api.v1.system.check_database", healthy_database)
    monkeypatch.setattr("app.api.v1.system.detect_device", lambda _selection: "cpu")
    monkeypatch.setattr("app.api.v1.system.get_llm_provider", lambda: FakeLLMProvider())
    monkeypatch.setattr(
        "app.services.ingestion.persistence.KnowledgeRepository.counts", empty_counts
    )
    monkeypatch.setattr(
        "app.services.retrieval.repository.RetrievalRepository.index_status",
        index_status,
    )
    monkeypatch.setattr(
        "app.services.retrieval.repository.RetrievalRepository.searchable_counts",
        searchable_counts,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json() == {
        "application": "online",
        "environment": "local",
        "database": {"connected": True, "detail": "ok"},
        "embeddings": {
            "provider": "sentence_transformers",
            "model": "BAAI/bge-small-en-v1.5",
            "dimension": 384,
            "device": "cpu",
            "loaded": False,
        },
        "reranker": {
            "provider": "sentence_transformers",
            "model": "cross-encoder/ms-marco-MiniLM-L6-v2",
            "device": "cpu",
            "enabled": True,
            "loaded": False,
        },
        "retrieval": {
            "algorithm_version": "hybrid-rrf-ce-v1",
            "reranking_enabled": True,
            "vector_index_available": True,
            "text_search_index_available": True,
            "searchable_sources": 0,
            "searchable_chunks": 0,
        },
        "llm": {
            "provider": "ollama",
            "model": "llama3.2:3b",
            "reachable": True,
            "model_available": True,
            "loaded": True,
            "detail": "ready",
            "model_variant": "base",
            "adapter_name": None,
            "adapter_version": None,
            "dataset_version": None,
            "model_manifest_checksum": None,
            "evaluation_status": "not_evaluated",
            "promotion_status": "created",
        },
        "knowledge": {
            "knowledge_sources": 0,
            "document_versions": 0,
            "chunks": 0,
            "completed_ingestion_jobs": 0,
            "failed_ingestion_jobs": 0,
        },
    }
