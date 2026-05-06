from app.db.session import SessionLocal, init_db
from app.schemas.agent import AgentQueryRequest
from app.services.agent.agent_service import AgentService

QUERIES = [
    "Why might async inference latency increase?",
    "How does the model registry work?",
    "What should I check if an eval job fails?",
]


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        service = AgentService(db)
        for query in QUERIES:
            response = service.query(AgentQueryRequest(query=query, top_k=3))
            print("=" * 80)
            print(query)
            print(response.final_answer)
            print(f"citations={len(response.citations)} approval={response.requires_human_approval}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
