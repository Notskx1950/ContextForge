from pydantic import BaseModel


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    title: str
    source_type: str
    source_uri: str | None = None
    score: float
    content_preview: str
