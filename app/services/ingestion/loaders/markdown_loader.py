from pathlib import Path
from typing import Any

from app.services.ingestion.loaders.base import BaseSourceLoader, LoadedDocument


class MarkdownLoader(BaseSourceLoader):
    def load_file(
        self,
        path: str | Path,
        base_dir: str | Path | None = None,
    ) -> LoadedDocument:
        file_path = Path(path).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        if file_path.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError(f"Expected a Markdown file, got: {file_path}")

        base_path = Path(base_dir).resolve() if base_dir else file_path.parent
        raw_text = file_path.read_text(encoding="utf-8")
        metadata = self._infer_metadata(file_path, base_path)

        return LoadedDocument(
            title=self._infer_title(file_path, raw_text),
            raw_text=raw_text,
            source_uri=str(file_path),
            source_type=metadata["doc_type"],
            metadata=metadata,
        )

    def _infer_title(self, path: Path, raw_text: str) -> str:
        for line in raw_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped.removeprefix("# ").strip()

        return path.stem.replace("-", " ").replace("_", " ").title()

    def _infer_metadata(self, path: Path, base_dir: Path) -> dict[str, Any]:
        relative_path = path.relative_to(base_dir)
        parts = [part.lower() for part in relative_path.parts]

        return {
            "path": str(relative_path),
            "filename": path.name,
            "extension": path.suffix.lower(),
            "repo": base_dir.name,
            "component": self._infer_component(relative_path),
            "doc_type": self._infer_doc_type(parts),
            "loader": "markdown_loader",
            "format": "markdown",
        }

    def _infer_doc_type(self, path_parts: list[str]) -> str:
        joined = "/".join(path_parts)

        if "runbook" in joined or "runbooks" in joined:
            return "runbook"

        if "incident" in joined or "incidents" in joined:
            return "incident_note"

        if "benchmark" in joined or "benchmarks" in joined or "logs" in joined:
            return "benchmark_log"

        if "architecture" in joined or "design" in joined:
            return "design_doc"

        return "markdown"

    def _infer_component(self, relative_path: Path) -> str:
        parts = relative_path.parts

        if len(parts) >= 2:
            return parts[-2].lower().replace(" ", "-")

        return "general"