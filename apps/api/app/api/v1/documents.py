from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.session import async_session_factory
from app.schemas.ingestion import (
    DocumentChunkResponse,
    DocumentDetailResponse,
    DocumentListItem,
    PaginatedChunksResponse,
    PaginatedDocumentsResponse,
    PaginationParams,
)
from app.services.ingestion.persistence import KnowledgeRepository

router = APIRouter(prefix="/documents", tags=["documents"])


def pagination(
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


PaginationDependency = Annotated[PaginationParams, Depends(pagination)]


@router.get("", response_model=PaginatedDocumentsResponse)
async def list_documents(params: PaginationDependency):
    async with async_session_factory() as session:
        total, documents = await KnowledgeRepository(session).list_documents(
            limit=params.limit, offset=params.offset
        )
        return PaginatedDocumentsResponse(
            total=total,
            limit=params.limit,
            offset=params.offset,
            items=[
                DocumentListItem(
                    id=document.id,
                    source_id=document.source_id,
                    source_type=document.source.source_type,
                    display_name=document.source.display_name,
                    source_status=document.source.status,
                    version=document.version,
                    title=document.title,
                    mime_type=document.mime_type,
                    content_checksum=document.content_checksum,
                    chunk_count=len(document.chunks),
                    ingested_at=document.created_at,
                )
                for document in documents
            ],
        )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: UUID):
    async with async_session_factory() as session:
        document = await KnowledgeRepository(session).get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        return DocumentDetailResponse(
            id=document.id,
            source_id=document.source_id,
            source_type=document.source.source_type,
            display_name=document.source.display_name,
            source_status=document.source.status,
            version=document.version,
            title=document.title,
            mime_type=document.mime_type,
            content_checksum=document.content_checksum,
            chunk_count=len(document.chunks),
            ingested_at=document.created_at,
            normalized_text_preview=document.normalized_text[:1200],
            extraction_metadata=document.extraction_metadata,
        )


@router.get("/{document_id}/chunks", response_model=PaginatedChunksResponse)
async def list_document_chunks(document_id: UUID, params: PaginationDependency):
    async with async_session_factory() as session:
        repo = KnowledgeRepository(session)
        if await repo.get_document(document_id) is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        total, chunks = await repo.list_chunks(
            document_id, limit=params.limit, offset=params.offset
        )
        return PaginatedChunksResponse(
            total=total,
            limit=params.limit,
            offset=params.offset,
            items=[
                DocumentChunkResponse(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    position=chunk.position,
                    heading_path=chunk.heading_path,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    chunk_checksum=chunk.chunk_checksum,
                    embedding_model=chunk.embedding_model,
                    chunk_metadata=chunk.chunk_metadata,
                    created_at=chunk.created_at,
                )
                for chunk in chunks
            ],
        )
