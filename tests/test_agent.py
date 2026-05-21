def test_agent_query_returns_grounded_answer_and_generation_metadata(client, ingested_document):
    response = client.post(
        "/agent/query",
        json={"query": "Why might async inference latency increase?", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["final_answer"]
    assert "Grounded answer based on retrieved ContextForge evidence" in body["final_answer"]
    assert "Mock grounded answer based on retrieved engineering context" not in body["final_answer"]

    assert body["citations"]
    assert body["trace_steps"]

    assert "unsupported_claims" in body
    assert body["unsupported_claims"] == []

    assert "generation_metadata" in body
    assert body["generation_metadata"]["provider"] == "mock"
    assert body["generation_metadata"]["citation_validation"] == "passed"
    assert body["generation_metadata"]["cited_chunk_count"] >= 1


def test_agent_query_refuses_when_no_context(client):
    response = client.post(
        "/agent/query",
        json={"query": "What does a nonexistent subsystem do?", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()

    assert "I do not have enough indexed context" in body["final_answer"]
    assert body["citations"] == []
    assert body["generation_metadata"]["reason"] == "no_context"
    assert body["generation_metadata"]["citation_validation"] == "no_context"