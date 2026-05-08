def test_ingest_markdown_preserves_heading_and_code_metadata(client):
    markdown = """# Async Inference
            ## Queue Design

            Async inference uses a worker queue.

            ```python
            def enqueue_job(job_id: str) -> None:
                print(job_id)
            ```
            """
    response = client.post(
        "/documents/ingest-markdown",
        json={
            "title": "Async inference runbook",
            "raw_text": markdown,
            "source_type": "runbook",
            "source_uri": "file://docs/runbooks/async-inference.md",
            "metadata": {"component": "inference"},
            "duplicate_policy": "skip",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] > 0
    assert body["chunk_count"] >= 2

    document = client.get(f"/documents/{body['document_id']}")
    assert document.status_code == 200

    chunks = document.json()["chunks"]
    assert any(chunk["metadata"].get("heading_path") for chunk in chunks)

    code_chunks = [chunk for chunk in chunks if chunk["metadata"].get("is_code")]
    assert code_chunks
    assert code_chunks[0]["metadata"]["language"] == "python"
    assert "def enqueue_job" in code_chunks[0]["content"]

def test_ingest_markdown_skip_duplicate_source_uri(client):
    payload = {
    "title": "Duplicate test",
    "raw_text": "# Duplicate\n\nSame source uri.",
    "source_type": "markdown",
    "source_uri": "file://docs/duplicate.md",
    "metadata": {"component": "test"},
    "duplicate_policy": "skip",
    }

    first = client.post("/documents/ingest-markdown", json=payload)
    second = client.post("/documents/ingest-markdown", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()
    second_body = second.json()

    assert first_body["action"] == "created"
    assert second_body["action"] == "skipped"
    assert second_body["document_id"] == first_body["document_id"]

def test_ingest_markdown_file(client, tmp_path):
    markdown_file = tmp_path / "async-inference.md"
    markdown_file.write_text(
    "# Async Inference\n\nLatency rises when queue depth increases.",
    encoding="utf-8",
    )

    response = client.post(
        "/documents/ingest-markdown-file",
        json={
            "path": str(markdown_file),
            "duplicate_policy": "skip",
            "metadata": {"repo": "contextforge-test"},
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["document_id"] > 0
    assert body["chunk_count"] >= 1
    assert body["action"] == "created"

    document = client.get(f"/documents/{body['document_id']}")
    assert document.status_code == 200

    document_body = document.json()
    assert document_body["title"] == "Async Inference"
    assert document_body["metadata"]["format"] == "markdown"
    assert document_body["metadata"]["repo"] == "contextforge-test"

def test_ingest_markdown_directory(client, tmp_path):
    docs_dir = tmp_path / "docs"
    runbooks_dir = docs_dir / "runbooks"
    runbooks_dir.mkdir(parents=True)

    (docs_dir / "architecture.md").write_text(
        "# Architecture\n\nContextForge uses FastAPI routes and services.",
        encoding="utf-8",
    )
    (runbooks_dir / "latency.md").write_text(
        "# Latency Runbook\n\nCheck queue depth and worker saturation.",
        encoding="utf-8",
    )

    response = client.post(
        "/documents/ingest-markdown-directory",
        json={
            "root_dir": str(docs_dir),
            "recursive": True,
            "duplicate_policy": "skip",
            "metadata": {"repo": "contextforge-test"},
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total_files"] == 2
    assert body["created"] == 2
    assert body["skipped"] == 0
    assert len(body["documents"]) == 2

def test_ingest_markdown_directory_skip_duplicates(client, tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "architecture.md").write_text(
        "# Architecture\n\nContextForge uses FastAPI routes and services.",
        encoding="utf-8",
    )

    payload = {
        "root_dir": str(docs_dir),
        "recursive": True,
        "duplicate_policy": "skip",
        "metadata": {"repo": "contextforge-test"},
    }

    first = client.post("/documents/ingest-markdown-directory", json=payload)
    second = client.post("/documents/ingest-markdown-directory", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["created"] == 1
    assert second.json()["created"] == 0
    assert second.json()["skipped"] == 1