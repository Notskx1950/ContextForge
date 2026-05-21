from sqlalchemy.orm import Session

from app.db.models import AgentRun, ToolCallRecord
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.services.agent.graph import AgentGraphRunner


class AgentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.runner = AgentGraphRunner(db)

    def query(self, request: AgentQueryRequest) -> AgentQueryResponse:
        state = self.runner.run(request.query, request.top_k)
        trace_steps = state.get("trace_steps", [])
        tool_calls = state.get("tool_calls", [])
        final_answer = state.get("final_answer", "")

        run = AgentRun(
            user_query=request.query,
            final_answer=final_answer,
            status="completed",
            trace_json={
                "steps": [step.model_dump() for step in trace_steps],
                "generation_metadata": state.get("generation_metadata", {}),
                "unsupported_claims": state.get("unsupported_claims", []),
            },
        )
        self.db.add(run)
        self.db.flush()

        for call in tool_calls:
            self.db.add(
                ToolCallRecord(
                    agent_run_id=run.id,
                    tool_name=call.tool_name,
                    input_json=call.input,
                    output_json=call.output,
                    status=call.status,
                )
            )
        self.db.commit()

        return AgentQueryResponse(
            run_id=run.id,
            final_answer=final_answer,
            citations=state.get("citations", []),
            trace_steps=trace_steps,
            tool_calls=tool_calls,
            requires_human_approval=state.get("requires_human_approval", False),
            unsupported_claims=state.get("unsupported_claims", []),
            generation_metadata=state.get("generation_metadata", {}),
        )
