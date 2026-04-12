from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.models.schemas import SourceDocument


class LocalSourceLoader:
    def __init__(self, source_dir: Path) -> None:
        self.source_dir = source_dir

    def load(self) -> list[SourceDocument]:
        documents: list[SourceDocument] = []
        for path in sorted(self.source_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue

            text = path.read_text(encoding="utf-8").strip()
            if not text:
                continue

            relative_path = path.relative_to(self.source_dir)
            source_type = "github" if "github" in relative_path.parts else "resume"
            source_url = self._extract_url(text)
            documents.append(
                SourceDocument(
                    id=self._build_id(relative_path, text),
                    title=self._derive_title(relative_path, text),
                    text=text,
                    source_type=source_type,
                    url=source_url,
                    metadata={"path": str(relative_path).replace("\\", "/")},
                )
            )
        return documents

    @staticmethod
    def _derive_title(relative_path: Path, text: str) -> str:
        for line in text.splitlines():
            if line.startswith("#"):
                return line.lstrip("#").strip()
        return relative_path.stem.replace("-", " ").replace("_", " ").title()

    @staticmethod
    def _build_id(relative_path: Path, text: str) -> str:
        digest = hashlib.sha1(f"{relative_path}:{text[:200]}".encode("utf-8")).hexdigest()[:10]
        return f"{relative_path.stem}-{digest}"

    @staticmethod
    def _extract_url(text: str) -> str | None:
        for prefix in ("Source URL:", "Source repository:", "Pull request URL:"):
            for line in text.splitlines():
                if line.startswith(prefix):
                    value = line.split(":", 1)[1].strip()
                    return value or None

        match = re.search(r"https?://\S+", text)
        return match.group(0) if match else None
