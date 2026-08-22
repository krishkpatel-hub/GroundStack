from groundstack_eval.metrics import evaluate_case


def test_rejects_fabricated_citation() -> None:
    result = evaluate_case(
        {
            "id": "case-1",
            "suite": "citations",
            "expected_answerability": "answerable",
            "expected_citations": ["S1"],
            "response": "Use it [S2].",
        }
    )

    assert result.passed is False
    assert "fabricated_citation" in result.failure_reasons


def test_accepts_abstention_without_citations() -> None:
    result = evaluate_case(
        {
            "id": "case-2",
            "suite": "abstention",
            "expected_answerability": "insufficient_evidence",
            "expected_citations": [],
            "response": "I do not have enough retrieved evidence to answer.",
        }
    )

    assert result.passed is True
