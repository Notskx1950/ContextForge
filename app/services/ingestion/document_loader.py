from pathlib import Path

from app.services.ingestion.loaders import LoadedDocument, MarkdownLoader


class DocumentLoader:
    """Facade / factory boundary for ingestion sources."""

    def __init__(self) -> None:
        self.markdown_loader = MarkdownLoader()

    def load_text(self, raw_text: str) -> str:
        return raw_text

    def load_markdown_file(
        self,
        path: str | Path,
        base_dir: str | Path | None = None,
    ) -> LoadedDocument:
        return self.markdown_loader.load_file(path, base_dir=base_dir)

    def load_markdown_directory(
        self,
        root_dir: str | Path,
        *,
        recursive: bool = True,
    ) -> list[LoadedDocument]:
        root_path = Path(root_dir).resolve()

        if not root_path.exists() or not root_path.is_dir():
            raise NotADirectoryError(f"Markdown directory not found: {root_path}")

        patterns = ["**/*.md", "**/*.markdown"] if recursive else ["*.md", "*.markdown"]
        files: list[Path] = []

        for pattern in patterns:
            files.extend(root_path.glob(pattern))

        unique_files = sorted(set(files))

        return [
            self.load_markdown_file(path, base_dir=root_path)
            for path in unique_files
        ]