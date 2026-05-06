def test_eval_endpoint_returns_placeholder_metrics(client):
    response = client.post("/evals/run", json={"name": "smoke", "dataset_name": "demo"})
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert "retrieval_hit_rate" in metrics
    assert "citation_coverage" in metrics
    assert "unsupported_claim_rate" in metrics
