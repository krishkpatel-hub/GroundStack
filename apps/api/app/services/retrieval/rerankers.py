import asyncio

from app.core.settings import get_settings
from app.services.ai.embeddings import detect_device
from app.services.ai.interfaces import Reranker
from app.services.ai.types import RetrievalCandidate, RetrievalQuery


class RerankerError(RuntimeError):
    def __init__(self, message: str, *, category: str = "reranker_error") -> None:
        super().__init__(message)
        self.category = category


class SentenceTransformerReranker(Reranker):
    def __init__(
        self,
        *,
        model_name: str | None = None,
        batch_size: int | None = None,
        device: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.reranker_model_name
        self.batch_size = batch_size or settings.reranker_batch_size
        self.device = detect_device(device or settings.reranker_device)
        self._model = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device=self.device)
        return self._model

    async def rerank(
        self, query: RetrievalQuery, candidates: list[RetrievalCandidate]
    ) -> list[RetrievalCandidate]:
        if not candidates:
            return []
        return await asyncio.to_thread(self._rerank_sync, query.text, candidates)

    def _rerank_sync(
        self, query_text: str, candidates: list[RetrievalCandidate]
    ) -> list[RetrievalCandidate]:
        try:
            model = self._load_model()
            pairs = [(query_text, candidate.chunk_content) for candidate in candidates]
            scores = model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)
        except Exception as exc:  # pragma: no cover - exercised through service fallback tests
            raise RerankerError(str(exc), category=type(exc).__name__) from exc
        ranked = [candidate.model_copy(deep=True) for candidate in candidates]
        for candidate, score in zip(ranked, scores, strict=True):
            candidate.reranker_score = float(score)
        return sorted(
            ranked,
            key=lambda item: (
                -(item.reranker_score or 0.0),
                -(item.rrf_score or 0.0),
                item.vector_rank if item.vector_rank is not None else 10**9,
                item.lexical_rank if item.lexical_rank is not None else 10**9,
                str(item.chunk_id),
            ),
        )


def get_reranker() -> SentenceTransformerReranker:
    return SentenceTransformerReranker()
