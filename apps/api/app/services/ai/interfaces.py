from abc import ABC, abstractmethod

from app.services.ai.types import (
    EmbeddingRequest,
    EmbeddingResult,
    GenerationEvent,
    GenerationRequest,
    GenerationResult,
    LLMHealth,
    RetrievalCandidate,
    RetrievalQuery,
    RetrievalResult,
)


class LLMProvider(ABC):
    @abstractmethod
    async def health(self) -> LLMHealth:
        raise NotImplementedError

    @abstractmethod
    async def model_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, request: GenerationRequest):
        if False:
            yield GenerationEvent(type="completed")
        raise NotImplementedError


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> list[EmbeddingResult]:
        raise NotImplementedError


class Retriever(ABC):
    @abstractmethod
    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        raise NotImplementedError


class Reranker(ABC):
    @abstractmethod
    async def rerank(
        self, query: RetrievalQuery, candidates: list[RetrievalCandidate]
    ) -> list[RetrievalCandidate]:
        raise NotImplementedError
