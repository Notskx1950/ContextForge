from app.schemas.agent import AgentTraceStep, ToolCallRead
from app.schemas.common import Citation
from app.schemas.retrieval import RetrievalRequest
from app.services.agent.state import AgentState
from app.services.retrieval.retriever_service import RetrieverService
from app.services.generation import GroundedAnswerComposer


def _trace(state: AgentState, node: str, message: str, data: dict | None = None) -> None:
    state.setdefault("trace_steps", []).append(
        AgentTraceStep(node=node, message=message, data=data or {})
    )


def classify_intent_node(state: AgentState) -> AgentState:
    query = state["user_query"].lower()
    if any(term in query for term in ["latency", "fail", "error", "why"]):
        intent = "debug"
    elif any(term in query for term in ["design", "architecture", "work"]):
        intent = "design"
    elif any(term in query for term in ["issue", "draft", "ticket"]):
        intent = "action_draft"
    else:
        intent = "qa"
    state["intent"] = intent
    _trace(state, "classify_intent", "Classified user intent with mock rules.", {"intent": intent})
    return state


def plan_retrieval_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "qa")
    plan = ["Search indexed engineering chunks", "Return citations", "Avoid unsupported claims"]
    if intent == "debug":
        plan.append("Prioritize runbooks, logs, and benchmark traces")
    state["retrieval_plan"] = plan
    _trace(state, "plan_retrieval", "Created a simple retrieval plan.", {"plan": plan})
    return state


def retrieve_context_node(state: AgentState, retriever: RetrieverService, top_k: int) -> AgentState:
    response = retriever.retrieve(RetrievalRequest(query=state["user_query"], top_k=top_k))
    state["retrieved_chunks"] = response.chunks
    _trace(
        state,
        "retrieve_context",
        "Retrieved context with mock keyword retriever.",
        {"chunk_count": len(response.chunks), "latency_ms": response.latency_ms},
    )
    return state


def execute_tools_node(state: AgentState) -> AgentState:
    tool_calls: list[ToolCallRead] = []
    if state.get("intent") == "action_draft":
        output = {
            "title": f"Investigate: {state['user_query'][:80]}",
            "body": "Draft issue generated from retrieved evidence. Human review required.",
            "labels": ["ai-draft", "needs-review"],
        }
        tool_calls.append(
            ToolCallRead(tool_name="draft_issue", input={"query": state["user_query"]}, output=output)
        )
        state["requires_human_approval"] = True
    else:
        state["requires_human_approval"] = False
    state["tool_calls"] = tool_calls
    _trace(state, "execute_tools", "Executed mock tools when required.", {"tool_calls": len(tool_calls)})
    return state


def verify_evidence_node(state: AgentState) -> AgentState:
    chunks = state.get("retrieved_chunks", [])
    score = round(min(sum(chunk.score for chunk in chunks[:3]) / 3, 1.0), 3) if chunks else 0.0
    state["evidence_score"] = score
    _trace(state, "verify_evidence", "Computed placeholder evidence score.", {"score": score})
    return state


def compose_answer_node(
    state: AgentState,
    composer: GroundedAnswerComposer | None = None,
) -> AgentState:
    composer = composer or GroundedAnswerComposer()

    composed = composer.compose(
        query=state["user_query"],
        context_chunks=state.get("retrieved_chunks", []),
        evidence_score=state.get("evidence_score", 0.0),
    )

    state["citations"] = composed.citations
    state["unsupported_claims"] = composed.unsupported_claims
    state["generation_metadata"] = composed.generation_metadata
    state["draft_answer"] = composed.answer
    state["final_answer"] = composed.answer

    _trace(
        state,
        "compose_answer",
        "Composed grounded answer with generation provider.",
        {
            "citation_count": len(composed.citations),
            "unsupported_claim_count": len(composed.unsupported_claims),
            "generation_metadata": composed.generation_metadata,
        },
    )

    return state
