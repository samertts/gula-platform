from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GenerateResult:
    files_created: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class BaseGenerator(ABC):
    def __init__(self, target_dir: str | Path, dry_run: bool = False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self._result = GenerateResult()

    @abstractmethod
    def generate(self, **kwargs: Any) -> GenerateResult: ...

    def _write(self, path: str | Path, content: str) -> None:
        full_path = self.target_dir / path
        if self.dry_run:
            self._result.files_created.append(str(full_path))
            return
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if full_path.exists():
            self._result.files_skipped.append(str(full_path))
            return
        full_path.write_text(content)
        self._result.files_created.append(str(full_path))

    def _ensure_dir(self, path: str | Path) -> Path:
        full_path = self.target_dir / path
        full_path.mkdir(parents=True, exist_ok=True)
        return full_path
