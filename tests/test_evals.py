def test_eval_endpoint_returns_retrieval_regression_metrics(client):
    response = client.post(
        "/evals/run",
        json={
            "name": "retrieval-v0.2",
            "dataset_name": "engineering-rag-smoke",
        },
    )

    assert response.status_code == 200
    metrics = response.json()["metrics"]

    assert metrics["query_count"] == 3
    assert metrics["recall_at_3"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["latency_ms"] >= 0