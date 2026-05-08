from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LoadedDocument:
    title: str
    raw_text: str
    source_uri: str
    source_type: str
    metadata: dict[str, Any]


class BaseSourceLoader(ABC):
    @abstractmethod
    def load_file(
        self,
        path: str | Path,
        base_dir: str | Path | None = None,
    ) -> LoadedDocument:
        raise NotImplementedError