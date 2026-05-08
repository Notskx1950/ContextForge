from __future__ import annotations

import os
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Important:
# This demo uses an isolated SQLite database so it does not pollute your normal
# local ContextForge database.
#
# This environment variable must be set before importing app.db.session.
# ---------------------------------------------------------------------------

DEMO_DB_PATH = Path("contextforge_architecture_demo.db")
os.environ["DATABASE_URL"] = f"sqlite:///./{DEMO_DB_PATH}"

from sqlalchemy.orm import Session, selectinload  # noqa: E402

from app.db.models import Document  # noqa: E402
from app.db.session import SessionLocal, init_db  # noqa: E402
from app.schemas.agent import AgentQueryRequest  # noqa: E402
from app.schemas.documents import IngestMarkdownDirectoryRequest  # noqa: E402
from app.schemas.retrieval import RetrievalRequest  # noqa: E402
from app.services.agent.agent_service import AgentService  # noqa: E402
from app.services.ingestion.ingestion_service import IngestionService  # noqa: E402
from app.services.retrieval.retriever_service import RetrieverService  # noqa: E402


DEMO_DOCS_DIR = Path("demo_architecture_docs")


def print_section(title: str, why: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("-" * 100)
    print(f"WHY: {why}")
    print("=" * 100)


def print_substep(title: str, why: str) -> None:
    print("\n" + "-" * 80)
    print(title)
    print(f"Why this matters: {why}")
    print("-" * 80)


def reset_demo_environment() -> None:
    print_section(
        "Step 0 — Prepare an isolated demo environment",
        (
            "We want the demo to be repeatable and beginner-friendly. "
            "Using a separate SQLite database means this script will not pollute "
            "the normal local development database."
        ),
    )

    if DEMO_DB_PATH.exists():
        DEMO_DB_PATH.unlink()
        print(f"Removed old demo database: {DEMO_DB_PATH}")

    init_db()
    print(f"Initialized demo database: {DEMO_DB_PATH}")


def write_demo_markdown_docs() -> None:
    print_section(
        "Step 1 — Create realistic Markdown engineering docs",
        (
            "A real RAG system usually does not ingest one toy string. "
            "It ingests engineering documents such as runbooks, architecture notes, "
            "benchmark reports, incident notes, and code snippets."
        ),
    )

    files = {
        DEMO_DOCS_DIR / "runbooks" / "inference" / "latency.md": """
            # Inference Latency Runbook

            ## Symptoms

            Async inference latency increases when queue depth grows and workers are saturated.

            ## First Checks

            Check queue depth, worker health, Redis connectivity, and retry pressure.

            ```powershell
            Get-Process python
            redis-cli LLEN inference_jobs
            ```

            ## Resolution

            Increase worker concurrency or reduce retrieval fanout before retrying the job.
        """,
        DEMO_DOCS_DIR / "architecture" / "retrieval" / "hybrid-retrieval.md": """
            # Hybrid Retrieval Design

            ## Overview

            ContextForge combines BM25 lexical retrieval with vector similarity search.

            BM25 is strong for exact terms such as API names, error codes, function names,
            and component names.

            Vector retrieval helps when the user query is a paraphrase of the document text.

            ## Score Fusion

            Hybrid retrieval normalizes BM25 scores and vector scores, then combines them
            with a weighted score.
        """,
        DEMO_DOCS_DIR / "benchmarks" / "evaluation" / "retrieval-fanout.md": """
            # Retrieval Fanout Benchmark

            ## Result

            Increasing retrieval fanout from 4 to 16 increased p95 latency.

            Queue wait time contributed more than model execution time.

            ## Recommendation

            Track retrieval latency, queue wait time, and reranker latency separately.
        """,
    }

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        cleaned = textwrap.dedent(content).strip() + "\n"
        path.write_text(cleaned, encoding="utf-8")
        print(f"Created demo Markdown file: {path}")

    print("\nCreated local docs tree:")
    print(
        textwrap.dedent(
            f"""
            {DEMO_DOCS_DIR}/
              runbooks/inference/latency.md
              architecture/retrieval/hybrid-retrieval.md
              benchmarks/evaluation/retrieval-fanout.md
            """
        ).strip()
    )


def ingest_markdown_directory(db: Session) -> None:
    print_section(
        "Step 2 — Ingest the Markdown directory through IngestionService",
        (
            "This demonstrates Phase 2. The API layer normally receives a request, "
            "but the important architecture is inside the service layer: "
            "IngestionService calls DocumentLoader, DocumentLoader delegates to "
            "MarkdownLoader, MarkdownLoader returns LoadedDocument, then the service "
            "chunks and persists Document / Chunk rows."
        ),
    )

    request = IngestMarkdownDirectoryRequest(
        root_dir=str(DEMO_DOCS_DIR),
        recursive=True,
        duplicate_policy="replace",
        metadata={"demo": "architecture_walkthrough"},
    )

    service = IngestionService(db)
    response = service.ingest_markdown_directory(request)

    print("Ingestion summary:")
    print(f"  root_dir    = {response.root_dir}")
    print(f"  total_files = {response.total_files}")
    print(f"  created     = {response.created}")
    print(f"  skipped     = {response.skipped}")
    print(f"  replaced    = {response.replaced}")
    print(f"  versioned   = {response.versioned}")

    print("\nPer-document results:")
    for item in response.documents:
        print(
            f"  action={item.action:<8} "
            f"document_id={item.document_id:<3} "
            f"chunks={item.chunk_count:<2} "
            f"title={item.title}"
        )


def load_demo_documents(db: Session) -> list[Document]:
    docs = (
        db.query(Document)
        .options(selectinload(Document.chunks))
        .order_by(Document.id)
        .all()
    )

    demo_root = str(DEMO_DOCS_DIR.resolve())
    return [
        doc
        for doc in docs
        if doc.source_uri is not None and str(doc.source_uri).startswith(demo_root)
    ]


def inspect_persisted_documents(db: Session) -> None:
    print_section(
        "Step 3 — Inspect persisted Document and Chunk records",
        (
            "A RAG system needs traceability. After ingestion, we should be able to see "
            "which source file created each Document, how many Chunks were generated, "
            "and what metadata was attached to each Chunk."
        ),
    )

    documents = load_demo_documents(db)

    for document in documents:
        print(f"\nDocument id={document.id}")
        print(f"  title       = {document.title}")
        print(f"  source_type = {document.source_type}")
        print(f"  source_uri  = {document.source_uri}")
        print(f"  metadata    = {document.metadata_json}")
        print(f"  chunks      = {len(document.chunks)}")

        for chunk in sorted(document.chunks, key=lambda item: item.chunk_index):
            metadata = chunk.metadata_json or {}
            preview = chunk.content.replace("\n", " ")[:120]
            print(
                f"    chunk_index={chunk.chunk_index:<2} "
                f"is_code={str(metadata.get('is_code')):<5} "
                f"heading={metadata.get('heading_path')!r}"
            )
            print(f"      preview={preview}")


def run_retrieval_case(
    retriever: RetrieverService,
    *,
    title: str,
    why: str,
    request: RetrievalRequest,
) -> None:
    print_substep(title, why)

    print("Retrieval request:")
    print(f"  query    = {request.query}")
    print(f"  strategy = {request.strategy}")
    print(f"  top_k    = {request.top_k}")
    print(f"  filters  = {request.filters.model_dump()}")

    response = retriever.retrieve(request)

    print("\nRetrieved chunks:")
    if not response.chunks:
        print("  No chunks returned.")
        return

    for index, chunk in enumerate(response.chunks, start=1):
        preview = chunk.content.replace("\n", " ")[:160]
        print(f"\n  [{index}] score={chunk.score} title={chunk.title}")
        print(f"      source_type = {chunk.source_type}")
        print(f"      metadata    = {chunk.metadata}")
        print(f"      preview     = {preview}")


def demonstrate_retrieval_strategies(db: Session) -> None:
    print_section(
        "Step 4 — Compare BM25, vector, and hybrid retrieval",
        (
            "This demonstrates Phase 3. BM25 is lexical retrieval, vector retrieval "
            "uses local deterministic embeddings and cosine similarity, and hybrid "
            "retrieval combines both scores. All strategies reuse the same filtering "
            "logic before scoring candidates."
        ),
    )

    retriever = RetrieverService(db)

    run_retrieval_case(
        retriever,
        title="4.1 BM25 retrieval — exact keyword matching",
        why=(
            "BM25 is strong when the query uses terms that appear directly in the "
            "document, such as queue, latency, worker, or saturation."
        ),
        request=RetrievalRequest(
            query="queue depth worker saturation latency",
            top_k=3,
            strategy="bm25",
            filters={"metadata": {"component": "inference"}},
        ),
    )

    run_retrieval_case(
        retriever,
        title="4.2 Vector retrieval — local semantic-ish matching",
        why=(
            "Vector retrieval is useful when the user query is phrased differently "
            "from the document. In this project it uses a deterministic local vectorizer, "
            "not a production embedding model, so it is best understood as a testable MVP."
        ),
        request=RetrievalRequest(
            query="why is inference slow under load",
            top_k=3,
            strategy="vector",
            filters={"metadata": {"component": "inference"}},
        ),
    )

    run_retrieval_case(
        retriever,
        title="4.3 Hybrid retrieval — combine lexical and vector signals",
        why=(
            "Hybrid retrieval balances exact keyword matching and vector similarity. "
            "This is a common production RAG pattern because BM25 and embeddings have "
            "different strengths."
        ),
        request=RetrievalRequest(
            query="semantic keyword fusion vector search",
            top_k=3,
            strategy="hybrid",
            filters={"metadata": {"component": "retrieval"}},
        ),
    )

    run_retrieval_case(
        retriever,
        title="4.4 Metadata filtering — narrow the search space before scoring",
        why=(
            "Filters run before scoring. This prevents unrelated documents from being "
            "scored and makes retrieval more controllable."
        ),
        request=RetrievalRequest(
            query="p95 latency retrieval fanout queue wait time",
            top_k=3,
            strategy="hybrid",
            filters={"metadata": {"component": "evaluation"}},
        ),
    )


def demonstrate_agent_workflow(db: Session) -> None:
    print_section(
        "Step 5 — Run the agent workflow on top of retrieval",
        (
            "The agent layer does not replace retrieval. It orchestrates retrieval, "
            "tool execution, evidence verification, and answer composition. The current "
            "agent is still a LangGraph-style sequential runner, not a full LangGraph runtime."
        ),
    )

    service = AgentService(db)
    response = service.query(
        AgentQueryRequest(
            query="Why might async inference latency increase under load?",
            top_k=3,
        )
    )

    print("Agent final answer:")
    print(response.final_answer)

    print("\nCitations:")
    for index, citation in enumerate(response.citations, start=1):
        print(
            f"  [{index}] title={citation.title} "
            f"chunk_id={citation.chunk_id} "
            f"score={citation.score}"
        )

    print("\nTrace steps:")
    for step in response.trace_steps:
        print(f"  node={step.node:<20} message={step.message}")


def print_final_architecture_summary() -> None:
    print_section(
        "Final architecture summary",
        (
            "This is the mental model you should keep after running the demo."
        ),
    )

    print(
        textwrap.dedent(
            """
            Phase 2 ingestion architecture:

            API request
              → IngestionService
              → DocumentLoader facade / factory
              → MarkdownLoader
              → LoadedDocument
              → chunk_markdown
              → Document / Chunk persistence


            Phase 3 retrieval architecture:

            /retrieval/query
              → RetrieverService
              → apply source_type / document_id / metadata filters
              → score candidates using one strategy:

                    keyword_mock  = old baseline
                    bm25          = lexical retrieval
                    vector        = local embedding + cosine similarity
                    hybrid        = normalized BM25 + normalized vector score

              → sort by score
              → rerank
              → return top_k RetrievedChunk objects
              → persist RetrievalRun


            Agent architecture:

            AgentService.query
              → AgentGraphRunner.run
              → classify_intent_node
              → plan_retrieval_node
              → retrieve_context_node
              → execute_tools_node
              → verify_evidence_node
              → compose_answer_node
              → AgentRun / ToolCallRecord persistence
            """
        ).strip()
    )


def main() -> None:
    reset_demo_environment()
    write_demo_markdown_docs()

    db = SessionLocal()
    try:
        ingest_markdown_directory(db)
        inspect_persisted_documents(db)
        demonstrate_retrieval_strategies(db)
        demonstrate_agent_workflow(db)
        print_final_architecture_summary()
    finally:
        db.close()


if __name__ == "__main__":
    main()