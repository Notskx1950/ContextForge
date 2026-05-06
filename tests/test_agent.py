def test_agent_query_returns_answer_and_citations(client, ingested_document):
    response = client.post(
        "/agent/query",
        json={"query": "Why might async inference latency increase?", "top_k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["final_answer"]
    assert body["citations"]
    assert body["trace_steps"]
