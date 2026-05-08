import re
from dataclasses import dataclass, field
from typing import Any

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^```(?P<lang>[A-Za-z0-9_+\-]*)\s*$")


@dataclass(frozen=True)
class ChunkDraft:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_text(raw_text: str, max_chars: int = 900) -> list[str]:
    """Simple paragraph-aware chunker for local demos."""
    paragraphs = [part.strip() for part in raw_text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs or [raw_text.strip()]:
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_markdown(raw_text: str, max_chars: int = 1200) -> list[ChunkDraft]:
    """Markdown-aware chunker.

    Goals:
    - Preserve heading context.
    - Keep fenced code blocks intact.
    - Attach metadata to each chunk.
    """
    chunks: list[ChunkDraft] = []
    heading_stack: list[str] = []
    text_buffer: list[str] = []
    code_buffer: list[str] = []
    in_code = False
    code_language = "plain"

    def heading_path() -> str:
        """Return the current heading path as a string."""
        return " > ".join(heading_stack)

    def flush_text() -> None:
        """Flush the text buffer into chunks, respecting the max_chars limit."""    
        nonlocal text_buffer

        text = "\n".join(text_buffer).strip()
        if not text:
            text_buffer = []
            return

        for part in chunk_text(text, max_chars=max_chars):
            chunks.append(
                ChunkDraft(
                    content=part,
                    metadata={
                        "chunker": "markdown_heading",
                        "heading_path": heading_path(),
                        "is_code": False,
                    },
                )
            )

        text_buffer = []

    def flush_code() -> None:
        """Flush the code buffer as a single chunk."""
        nonlocal code_buffer

        code_text = "\n".join(code_buffer).strip()
        if code_text:
            chunks.append(
                ChunkDraft(
                    content=code_text,
                    metadata={
                        "chunker": "markdown_code_fence",
                        "heading_path": heading_path(),
                        "is_code": True,
                        "language": code_language or "plain",
                    },
                )
            )

        code_buffer = []

    for line in raw_text.splitlines():
        stripped = line.strip()
        fence_match = FENCE_RE.match(stripped)

        if fence_match:
            if in_code:
                code_buffer.append(line)
                flush_code()
                in_code = False
                code_language = "plain"
            else:
                flush_text()
                in_code = True
                code_language = fence_match.group("lang") or "plain"
                code_buffer = [line]
            continue

        if in_code:
            code_buffer.append(line)
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush_text()

            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            heading_stack = heading_stack[: level - 1] + [title]

            text_buffer.append(line)
            continue

        text_buffer.append(line)

    if in_code:
        flush_code()
    else:
        flush_text()

    return chunks