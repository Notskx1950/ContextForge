from sqlalchemy.orm import Session

from app.services.agent.nodes import (
    classify_intent_node,
    compose_answer_node,
    execute_tools_node,
    plan_retrieval_node,
    retrieve_context_node,
    verify_evidence_node,
)
from app.services.agent.state import AgentState
from app.services.retrieval.retriever_service import RetrieverService


class AgentGraphRunner:
    """LangGraph-style sequential runner.

    TODO: Replace this with langgraph.graph.StateGraph, durable checkpoints, streaming events,
    conditional edges, and human-in-the-loop interrupts.
    """

    def __init__(self, db: Session) -> None:
        self.retriever = RetrieverService(db)

    def run(self, user_query: str, top_k: int) -> AgentState:
        state: AgentState = {"user_query": user_query, "trace_steps": []}
        state = classify_intent_node(state)
        state = plan_retrieval_node(state)
        state = retrieve_context_node(state, self.retriever, top_k)
        state = execute_tools_node(state)
        state = verify_evidence_node(state)
        state = compose_answer_node(state)
        return state
