from typing import Literal

from app.core.settings import get_settings
from app.services.ai.interfaces import EmbeddingProvider
from app.services.ai.types import EmbeddingRequest, EmbeddingResult
from app.services.ingestion.types import EmbeddingError


def detect_device(selection: str) -> str:
    if selection != "auto":
        return selection
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        return "cpu"
    return "cpu"


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        *,
        model_name: str | None = None,
        dimension: int | None = None,
        batch_size: int | None = None,
        device: str | None = None,
    ) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model_name
        self.dimension = dimension or settings.embedding_dimension
        self.batch_size = batch_size or settings.embedding_batch_size
        self.device = detect_device(device or settings.embedding_device)
        self._model = None

    @property
    def active_model(self) -> str:
        return self.model_name

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    async def embed(self, request: EmbeddingRequest) -> list[EmbeddingResult]:
        return await self.embed_texts(request.inputs, mode="document")

    async def embed_texts(
        self, inputs: list[str], *, mode: Literal["document", "query"] = "document"
    ) -> list[EmbeddingResult]:
        import asyncio

        return await asyncio.to_thread(self._embed_sync, inputs, mode)

    async def embed_query(self, query: str) -> EmbeddingResult:
        return (await self.embed_texts([query], mode="query"))[0]

    def _embed_sync(self, inputs: list[str], mode: str) -> list[EmbeddingResult]:
        model = self._load_model()
        prompts = getattr(model, "prompts", {}) or {}
        if mode == "query" and "query" in prompts:
            prompt_name = "query"
        elif mode == "document" and "document" in prompts:
            prompt_name = "document"
        elif mode == "document" and "passage" in prompts:
            prompt_name = "passage"
        else:
            prompt_name = None
        encode_kwargs = {
            "batch_size": self.batch_size,
            "normalize_embeddings": True,
            "convert_to_numpy": True,
            "show_progress_bar": False,
        }
        try:
            if prompt_name is None:
                vectors = model.encode(inputs, **encode_kwargs)
            else:
                vectors = model.encode(inputs, prompt_name=prompt_name, **encode_kwargs)
        except TypeError:
            vectors = model.encode(inputs, **encode_kwargs)
        results: list[EmbeddingResult] = []
        for text, vector in zip(inputs, vectors, strict=True):
            values = [float(value) for value in vector.tolist()]
            if len(values) != self.dimension:
                raise EmbeddingError(
                    "Embedding dimension mismatch.",
                    safe_details={
                        "expected": self.dimension,
                        "actual": len(values),
                        "model": self.model_name,
                    },
                )
            results.append(EmbeddingResult(text=text, vector=values))
        return results


def get_embedding_provider() -> SentenceTransformerEmbeddingProvider:
    return SentenceTransformerEmbeddingProvider()
