from load.assertions import (
    validate_chat_stream,
    validate_discord_response,
    validate_retrieval_response,
)


def test_chat_stream_requires_terminal_event() -> None:
    result = validate_chat_stream(b'event: token\ndata: {"token":"hello"}\n\n')

    assert not result.ok


def test_chat_stream_accepts_canonical_answer_and_completion() -> None:
    body = (
        b'event: canonical_answer\ndata: {"request_id":"r1","grounding_status":"fully_grounded",'
        b'"citations":[]}\n\n'
        b'event: completed\ndata: {"request_id":"r1"}\n\n'
    )

    assert validate_chat_stream(body).ok


def test_retrieval_citation_schema_is_validated() -> None:
    payload = {"query": "x", "citations": [{"citation_id": "S1", "title": "Guide"}]}

    assert validate_retrieval_response(payload).ok
    assert not validate_retrieval_response({"query": "x", "citations": [{"title": "Guide"}]}).ok


def test_discord_response_disallows_mentions() -> None:
    assert validate_discord_response({"type": 1}).ok
    assert not validate_discord_response(
        {"type": 4, "data": {"allowed_mentions": {"parse": ["everyone"]}}}
    ).ok
