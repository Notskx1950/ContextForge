class DocumentLoader:
    """Placeholder loader boundary for future ingestion sources."""

    def load_text(self, raw_text: str) -> str:
        return raw_text

    # TODO: Add Markdown, PDF, GitHub repo, issue, PR, benchmark-log, and runbook loaders.
    # TODO: Normalize source metadata such as repo, path, line ranges, commit SHA, and timestamps.
