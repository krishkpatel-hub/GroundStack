from collections.abc import AsyncIterator
from dataclasses import dataclass
from time import perf_counter
from uuid import UUID

from app.core.settings import get_settings
from app.db.session import async_session_factory
from app.services.ai.llm import LLMProviderError, get_llm_provider
from app.services.ai.types import ChatMessage, GenerationRequest, RetrievalFilters, RetrievalQuery
from app.services.generation.citations import validate_answer_citations
from app.services.generation.context import ApproximateTokenCounter, build_context
from app.services.generation.persistence import ConversationRepository
from app.services.generation.prompts import load_prompt_template, render_user_prompt
from app.services.retrieval.service import HybridRetriever


@dataclass
class ChatEvent:
    event: str
    data: dict[str, object]


def _ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 3)


def _citation_map(citations):
    return {citation.citation_id: citation for citation in citations}


class GroundedAnswerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm_provider = get_llm_provider()
        self.retriever = HybridRetriever()

    async def answer(
        self,
        *,
        question: str,
        conversation_id: UUID | None,
        client_request_id: str | None,
        filters: RetrievalFilters,
        owner_subject: str | None = None,
    ) -> dict[str, object]:
        final_event: dict[str, object] | None = None
        async for event in self.stream_answer(
            question=question,
            conversation_id=conversation_id,
            client_request_id=client_request_id,
            filters=filters,
            owner_subject=owner_subject,
        ):
            if event.event in {"canonical_answer", "error"}:
                final_event = event.data
        return final_event or {"grounding_status": "generation_failed", "answer": ""}

    async def stream_answer(
        self,
        *,
        question: str,
        conversation_id: UUID | None,
        client_request_id: str | None,
        filters: RetrievalFilters,
        owner_subject: str | None = None,
    ) -> AsyncIterator[ChatEvent]:
        sequence = 0
        request_id = client_request_id or "request"

        def event(name: str, **data: object) -> ChatEvent:
            nonlocal sequence
            sequence += 1
            return ChatEvent(
                event=name, data={"request_id": request_id, "sequence": sequence, **data}
            )

        async with async_session_factory() as session:
            repo = ConversationRepository(session)
            conversation = await repo.get_or_create_conversation(
                conversation_id, question, owner_subject
            )
            existing_messages = await repo.list_messages(conversation.id)
            user_message = await repo.create_user_message(
                conversation=conversation, content=question, client_request_id=client_request_id
            )
            await session.commit()
            conversation_id = conversation.id
            user_message_id = user_message.id

        yield event(
            "conversation",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
        )
        yield event("retrieval_started", conversation_id=str(conversation_id))

        try:
            retrieval = await self.retriever.retrieve(
                RetrievalQuery(
                    text=question,
                    limit=self.settings.retrieval_final_top_k,
                    filters=filters,
                    include_debug=True,
                )
            )
        except Exception as exc:
            async with async_session_factory() as session:
                repo = ConversationRepository(session)
                conversation = await repo.get_or_create_conversation(
                    conversation_id, question, owner_subject
                )
                message = await repo.create_assistant_message(
                    conversation=conversation,
                    content="Retrieval failed, so GroundStack cannot generate a grounded answer.",
                    status="failed",
                    grounding_status="retrieval_failed",
                    retrieval_run_id=None,
                    generation_run_id=None,
                    provider=None,
                    model=None,
                    prompt_version=None,
                    failure={"category": type(exc).__name__},
                )
                await session.commit()
            yield event(
                "error",
                conversation_id=str(conversation_id),
                message_id=str(message.id),
                grounding_status="retrieval_failed",
                message="Retrieval failed.",
            )
            return

        yield event(
            "retrieval_completed",
            conversation_id=str(conversation_id),
            retrieval_run_id=str(retrieval.retrieval_run_id),
            result_count=retrieval.result_count,
            citations=[citation.model_dump(mode="json") for citation in retrieval.citations],
        )

        if not retrieval.evidence_found:
            answer = (
                "I do not have enough retrieved evidence to answer this question. "
                "Add or select relevant documentation in the Knowledge Base, then search again."
            )
            async with async_session_factory() as session:
                repo = ConversationRepository(session)
                conversation = await repo.get_or_create_conversation(
                    conversation_id, question, owner_subject
                )
                message = await repo.create_assistant_message(
                    conversation=conversation,
                    content=answer,
                    status="completed",
                    grounding_status="insufficient_evidence",
                    retrieval_run_id=retrieval.retrieval_run_id,
                    generation_run_id=None,
                    provider=None,
                    model=None,
                    prompt_version=None,
                )
                await session.commit()
            payload = {
                "conversation_id": str(conversation_id),
                "message_id": str(message.id),
                "answer": answer,
                "grounding_status": "insufficient_evidence",
                "citations": [],
            }
            yield event("canonical_answer", **payload)
            yield event("completed", **payload)
            return

        template = load_prompt_template(self.settings.generation_prompt_version)
        counter = ApproximateTokenCounter()
        history = [
            ChatMessage(role=message.role, content=message.content)
            for message in existing_messages
            if message.status == "completed"
        ]
        context = build_context(
            retrieval=retrieval,
            history=history,
            context_window=self.settings.llm_context_window,
            max_output_tokens=self.settings.llm_max_output_tokens,
            system_prompt_tokens=counter.count(template.system),
            question_tokens=counter.count(question),
            max_history_messages=self.settings.max_conversation_history_messages,
        )
        user_prompt = render_user_prompt(
            template, question=question, history=context.history_text, sources=context.sources_text
        )
        allowed_citations = [
            citation
            for citation in retrieval.citations
            if citation.citation_id in context.included_citation_ids
        ]
        rendered_prompt = (
            f"{template.system}\n\n{user_prompt}"
            if self.settings.store_generation_prompts
            else None
        )

        async with async_session_factory() as session:
            repo = ConversationRepository(session)
            generation_run = await repo.create_generation_run(
                conversation_id=conversation_id,
                retrieval_run_id=retrieval.retrieval_run_id,
                provider=self.settings.llm_provider,
                model=self.settings.llm_model,
                prompt_version=template.version,
                prompt_checksum=template.checksum,
                parameters={
                    "temperature": self.settings.llm_temperature,
                    "top_p": self.settings.llm_top_p,
                    "max_tokens": self.settings.llm_max_output_tokens,
                },
                context_citation_ids=context.included_citation_ids,
                context_token_count=context.token_count,
                token_counting_mode=context.token_counting_mode,
                rendered_prompt=rendered_prompt,
            )
            await session.commit()
            generation_run_id = generation_run.id

        yield event(
            "generation_started",
            conversation_id=str(conversation_id),
            generation_run_id=str(generation_run_id),
            prompt_version=template.version,
            context_citation_ids=context.included_citation_ids,
            token_counting_mode=context.token_counting_mode,
        )

        generation_request = GenerationRequest(
            messages=[
                ChatMessage(role="system", content=template.system),
                ChatMessage(role="user", content=user_prompt),
            ],
            max_tokens=self.settings.llm_max_output_tokens,
            temperature=self.settings.llm_temperature,
            top_p=self.settings.llm_top_p,
            stream=True,
            request_id=request_id,
        )
        generation_start = perf_counter()
        first_token_latency_ms: float | None = None
        answer_parts: list[str] = []
        input_tokens: int | None = None
        output_tokens: int | None = None
        finish_reason: str | None = None
        async for provider_event in self.llm_provider.stream(generation_request):
            if provider_event.type == "token" and provider_event.token:
                if first_token_latency_ms is None:
                    first_token_latency_ms = _ms(generation_start)
                answer_parts.append(provider_event.token)
                yield event("token", token=provider_event.token)
            elif provider_event.type == "usage":
                input_tokens = provider_event.input_tokens
                output_tokens = provider_event.output_tokens
                yield event("usage", input_tokens=input_tokens, output_tokens=output_tokens)
            elif provider_event.type == "error":
                async with async_session_factory() as session:
                    repo = ConversationRepository(session)
                    conversation = await repo.get_or_create_conversation(
                        conversation_id, question, owner_subject
                    )
                    message = await repo.create_assistant_message(
                        conversation=conversation,
                        content=(
                            "Generation is unavailable, but retrieved evidence is available above."
                        ),
                        status="failed",
                        grounding_status="generation_failed",
                        retrieval_run_id=retrieval.retrieval_run_id,
                        generation_run_id=generation_run_id,
                        provider=self.settings.llm_provider,
                        model=self.settings.llm_model,
                        prompt_version=template.version,
                        failure={
                            "category": provider_event.error_category,
                            "message": provider_event.error_message,
                        },
                    )
                    run = await session.get(type(generation_run), generation_run_id)
                    await repo.complete_generation_run(
                        run,
                        status="failed",
                        message_id=message.id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        first_token_latency_ms=first_token_latency_ms,
                        total_latency_ms=_ms(generation_start),
                        finish_reason=None,
                        repair_attempt_count=0,
                        error={
                            "category": provider_event.error_category,
                            "message": provider_event.error_message,
                        },
                    )
                    await session.commit()
                yield event(
                    "error",
                    conversation_id=str(conversation_id),
                    message_id=str(message.id),
                    grounding_status="generation_failed",
                    message=provider_event.error_message or "Generation failed.",
                )
                return
            elif provider_event.type == "completed":
                finish_reason = provider_event.finish_reason
                if provider_event.content and not answer_parts:
                    answer_parts.append(provider_event.content)

        provisional = "".join(answer_parts).strip()
        validation = validate_answer_citations(provisional, allowed_citations)
        repair_attempts = 0
        canonical = provisional
        if not validation.valid and provisional:
            repair_attempts = 1
            allowed = ", ".join(context.included_citation_ids)
            repair_prompt = (
                f"Allowed citation IDs: {allowed}\n\n"
                "Correct the answer below by adding only allowed citations. "
                "Do not add new facts. If citations cannot support it, abstain.\n\n"
                f"{provisional}"
            )
            try:
                repaired = await self.llm_provider.generate(
                    GenerationRequest(
                        messages=[
                            ChatMessage(role="system", content=template.system),
                            ChatMessage(role="user", content=repair_prompt),
                        ],
                        max_tokens=self.settings.llm_max_output_tokens,
                        temperature=0.0,
                        top_p=1.0,
                    )
                )
                repaired_validation = validate_answer_citations(repaired.content, allowed_citations)
                if repaired_validation.valid:
                    canonical = repaired.content
                    validation = repaired_validation
            except LLMProviderError:
                pass

        grounding_status = (
            validation.grounding_status if validation.valid else "citation_validation_failed"
        )
        status = "completed" if validation.valid else "failed"
        used = [
            citation
            for citation in allowed_citations
            if citation.citation_id in set(validation.used_citation_ids)
        ]

        async with async_session_factory() as session:
            repo = ConversationRepository(session)
            conversation = await repo.get_or_create_conversation(
                conversation_id, question, owner_subject
            )
            message = await repo.create_assistant_message(
                conversation=conversation,
                content=canonical,
                status=status,
                grounding_status=grounding_status,
                retrieval_run_id=retrieval.retrieval_run_id,
                generation_run_id=generation_run_id,
                provider=self.settings.llm_provider,
                model=self.settings.llm_model,
                prompt_version=template.version,
                token_usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
                failure=None
                if validation.valid
                else {"fabricated_citations": validation.fabricated_citation_ids},
            )
            if validation.valid:
                await repo.add_message_citations(message_id=message.id, citations=used)
            run = await session.get(type(generation_run), generation_run_id)
            await repo.complete_generation_run(
                run,
                status=status,
                message_id=message.id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                first_token_latency_ms=first_token_latency_ms,
                total_latency_ms=_ms(generation_start),
                finish_reason=finish_reason,
                repair_attempt_count=repair_attempts,
                error=None if validation.valid else {"grounding_status": grounding_status},
            )
            await session.commit()

        payload = {
            "conversation_id": str(conversation_id),
            "message_id": str(message.id),
            "generation_run_id": str(generation_run_id),
            "answer": canonical,
            "grounding_status": grounding_status,
            "citations": [citation.model_dump(mode="json") for citation in used],
            "repair_attempts": repair_attempts,
        }
        yield event("canonical_answer", **payload)
        yield event("completed", **payload)
