from __future__ import annotations

import json
import os
import random
from itertools import cycle
from pathlib import Path
from typing import Any

from load.assertions import (
    validate_chat_stream,
    validate_discord_response,
    validate_retrieval_response,
)
from locust import HttpUser, between, task
from locust.exception import StopUser


def _questions() -> cycle[dict[str, Any]]:
    path = Path(os.getenv("GROUNDSTACK_LOAD_QUESTIONS", "load/datasets/questions_smoke.jsonl"))
    seed = int(os.getenv("GROUNDSTACK_LOAD_SEED", "1201"))
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    random.Random(seed).shuffle(rows)
    return cycle(rows)


QUESTION_ITER = _questions()
MAX_REQUESTS = int(os.getenv("GROUNDSTACK_LOAD_MAX_REQUESTS", "5"))
REQUEST_COUNT = 0

if MAX_REQUESTS <= 0:
    raise RuntimeError("GROUNDSTACK_LOAD_MAX_REQUESTS must be positive.")


def _next_question() -> dict[str, Any]:
    global REQUEST_COUNT
    if REQUEST_COUNT >= MAX_REQUESTS:
        raise StopUser()
    REQUEST_COUNT += 1
    return next(QUESTION_ITER)


class GroundStackUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def retrieval_search(self) -> None:
        item = _next_question()
        with self.client.post(
            "/api/v1/retrieval/search",
            json={"query": item["question"], "top_k": 5, "filters": {}, "include_debug": False},
            name="/api/v1/retrieval/search",
            catch_response=True,
        ) as response:
            if response.status_code >= 500:
                response.failure(f"server error {response.status_code}")
                return
            if response.status_code >= 400:
                response.success()
                return
            result = validate_retrieval_response(response.json())
            if result.ok:
                response.success()
            else:
                response.failure(result.reason)

    @task(4)
    def chat_stream(self) -> None:
        item = _next_question()
        with self.client.post(
            "/api/v1/chat/stream",
            json={
                "question": item["question"],
                "filters": {},
                "client_request_id": f"load-{item['id']}-{REQUEST_COUNT}",
            },
            stream=True,
            name="/api/v1/chat/stream",
            catch_response=True,
        ) as response:
            body = b"".join(response.iter_content(chunk_size=None))
            if response.status_code >= 500:
                response.failure(f"server error {response.status_code}")
                return
            result = validate_chat_stream(body)
            if result.ok:
                response.success()
            else:
                response.failure(result.reason)

    @task(1)
    def status_check(self) -> None:
        _next_question()
        with self.client.get(
            "/api/v1/system/status",
            name="/api/v1/system/status",
            catch_response=True,
        ) as response:
            if response.status_code == 200 and response.json().get("status"):
                response.success()
            else:
                response.failure("status endpoint missing status")

    @task(1)
    def discord_ping_mock(self) -> None:
        _next_question()
        payload = {"type": 1}
        with self.client.post(
            "/integrations/discord/interactions",
            json=payload,
            headers={
                "x-signature-timestamp": "0",
                "x-signature-ed25519": "invalid-local-load-test",
            },
            name="/integrations/discord/interactions.invalid-signature",
            catch_response=True,
        ) as response:
            if response.status_code == 401:
                response.success()
                return
            try:
                result = validate_discord_response(response.json())
            except Exception:
                result = validate_discord_response({})
            if result.ok:
                response.success()
            else:
                response.failure(result.reason)
