from __future__ import annotations

import json
import os
from itertools import cycle
from pathlib import Path

from locust import HttpUser, between, task


def _questions() -> cycle[str]:
    path = Path(os.getenv("GROUNDSTACK_LOAD_QUESTIONS", "load/questions_smoke.jsonl"))
    rows = [json.loads(line)["question"] for line in path.read_text(encoding="utf-8").splitlines()]
    return cycle(rows)


QUESTION_ITER = _questions()


class GroundStackUser(HttpUser):
    wait_time = between(1, 3)

    @task(2)
    def retrieval_search(self) -> None:
        question = next(QUESTION_ITER)
        self.client.post(
            "/api/v1/retrieval/search",
            json={"query": question, "top_k": 5, "filters": {}, "include_debug": False},
            name="/api/v1/retrieval/search",
        )

    @task(1)
    def chat(self) -> None:
        question = next(QUESTION_ITER)
        with self.client.post(
            "/api/v1/chat/stream",
            json={"question": question, "filters": {}},
            stream=True,
            name="/api/v1/chat/stream",
            catch_response=True,
        ) as response:
            body = b"".join(response.iter_content(chunk_size=None))
            if response.status_code >= 500:
                response.failure(f"server error {response.status_code}")
            elif b"event: completed" not in body and b"event: error" not in body:
                response.failure("stream did not terminate with completed or error event")
