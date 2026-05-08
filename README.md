# ContextForge

ContextForge is an agentic RAG backend skeleton for engineering teams. It ingests engineering documents, source-code snippets, logs, and evaluation traces; retrieves relevant context; and runs a LangGraph-style workflow to produce grounded answers with citations and optional tool calls.

This repository is intentionally a framework-level skeleton. The current implementation uses mock embeddings, mock retrieval, mock tools, and a sequential graph runner so the system can run locally without OpenAI keys, pgvector, Redis workers, or LangGraph runtime setup.

## Why This Project Exists

Most RAG demos stop at document upload and chat. ContextForge is structured like a production AI engineering backend: explicit API contracts, service boundaries, adapter interfaces, database models, retrieval traces, agent traces, tool-call records, and evaluation hooks.

## Architecture

```text
FastAPI
  |-- /documents  -> IngestionService -> Document / Chunk tables
  |-- /retrieval  -> RetrieverService -> keyword mock now, pgvector/hybrid later
  |-- /agent      -> AgentService -> LangGraph-style state/nodes/tools
  |-- /evals      -> EvalService -> placeholder metrics now, Ragas later

Adapters
  |-- BaseEmbeddingProvider / MockEmbeddingProvider
  |-- BaseVectorStore / InMemoryVectorStore placeholder
  |-- BaseReranker / NoOpReranker
  |-- BaseTool / SearchDocsTool / GetChunkByIdTool / DraftIssueTool

Storage
  |-- SQLite for local tests
  |-- PostgreSQL-ready SQLAlchemy schema
  |-- pgvector-ready design, not required for v1 skeleton
  |-- Redis/RQ-ready docker service, mock worker mode initially
```

## Quickstart

From `O:\Project\AtlasAgent\contextforge`:

```powershell
..\.venv\Scripts\python.exe -m pip install -e .[dev]
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe scripts\seed_demo_data.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Example API Calls

```bash
curl -X POST http://127.0.0.1:8000/documents/ingest-text \
  -H "Content-Type: application/json" \
  -d '{"title":"Async inference design","raw_text":"Async inference uses worker queues. Latency rises when queue depth increases.","source_type":"design_doc","metadata":{"component":"inference"}}'
```

```bash
curl -X POST http://127.0.0.1:8000/retrieval/query \
  -H "Content-Type: application/json" \
  -d '{"query":"async inference latency queue","top_k":3,"strategy":"keyword_mock"}'
```

```bash
curl -X POST http://127.0.0.1:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Why might async inference latency increase?","top_k":3}'
```

## Current Mock Implementation Status

- Ingestion: raw text only, paragraph-aware chunking.
- Retrieval: naive keyword matching against stored chunks.
- Embeddings: mock interface only; no real vector persistence yet.
- Reranking: no-op adapter.
- Agent: sequential LangGraph-style state runner with explicit nodes.
- Tools: draft-only mock tools; no external writes.
- Evaluation: placeholder metrics for smoke testing.

## Roadmap

- Add Markdown, PDF, GitHub repo, issue, PR, runbook, benchmark-log ingestion.
- Add real embedding providers and async embedding jobs.
- Add PostgreSQL + pgvector vector search.
- Add BM25, hybrid score fusion, metadata filtering, query rewriting, and reranking.
- Replace sequential graph runner with LangGraph StateGraph, checkpoints, streaming, and human approval interrupts.
- Add GitHub issue/PR draft integrations behind human approval.
- Add Ragas metrics: faithfulness, answer relevancy, context precision, context recall.
- Add agent metrics: tool accuracy, task completion, latency, cost, and failure categories.

## Evaluation Plan

ContextForge will evolve toward a regression-driven RAG platform:

- Retrieval: hit rate, Recall@k, MRR, context precision, context recall.
- Generation: faithfulness, answer relevancy, citation coverage, unsupported claim rate.
- Agent: tool selection accuracy, task completion rate, human approval rate, latency, cost per query.

## Engineering Tradeoffs

- SQLite keeps local tests simple, while SQLAlchemy models stay PostgreSQL-ready.
- pgvector is intentionally not required yet, so contributors can run the skeleton without database extensions.
- Mock adapters keep the API stable while allowing future embedding/vector/LLM providers to be swapped in.
- The agent graph is explicit and auditable before adding LangGraph runtime complexity.
- Action tools produce drafts only to avoid unsafe external side effects.
