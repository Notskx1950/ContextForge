def test_ingest_text_creates_document_and_chunks(client):
    response = client.post(
        "/documents/ingest-text",
        json={
            "title": "Model registry design",
            "raw_text": "The model registry tracks model versions, metadata, approvals, and eval reports.",
            "source_type": "design_doc",
            "metadata": {"team": "ml-platform"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] > 0
    assert body["chunk_count"] >= 1

    document = client.get(f"/documents/{body['document_id']}")
    assert document.status_code == 200
    assert document.json()["title"] == "Model registry design"
    assert len(document.json()["chunks"]) >= 1
