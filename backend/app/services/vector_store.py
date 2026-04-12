from __future__ import annotations

import json
from typing import Literal

import numpy as np

from app.core.config import Settings
from app.models.schemas import DocumentChunk

try:  # pragma: no cover - exercised when faiss is installed
    import faiss  # type: ignore
except Exception:  # pragma: no cover - fallback path
    faiss = None


class VectorStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.backend: Literal["faiss", "numpy"] = "faiss" if faiss is not None else "numpy"
        self.dimension: int | None = None
        self.chunks: list[DocumentChunk] = []
        self._index = None
        self._matrix: np.ndarray | None = None

    @property
    def ready(self) -> bool:
        return bool(self.chunks) and (self._index is not None or self._matrix is not None)

    def rebuild(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if not chunks or not embeddings:
            raise ValueError("Cannot build a vector index without chunks and embeddings.")

        matrix = np.asarray(embeddings, dtype=np.float32)
        self._normalize(matrix)
        self.dimension = int(matrix.shape[1])
        self.chunks = chunks

        if self.backend == "faiss":
            index = faiss.IndexFlatIP(self.dimension)
            index.add(matrix)
            self._index = index
            self._matrix = None
        else:
            self._matrix = matrix
            self._index = None

        self.save()

    def search(self, query_embedding: list[float], top_k: int) -> list[tuple[DocumentChunk, float]]:
        if not self.ready:
            return []

        vector = np.asarray([query_embedding], dtype=np.float32)
        self._normalize(vector)

        if self.backend == "faiss" and self._index is not None:
            scores, indices = self._index.search(vector, min(top_k, len(self.chunks)))
            ranked_indices = indices[0].tolist()
            ranked_scores = scores[0].tolist()
        else:
            assert self._matrix is not None
            similarity = vector @ self._matrix.T
            ranked_indices = np.argsort(similarity[0])[::-1][:top_k].tolist()
            ranked_scores = [float(similarity[0][index]) for index in ranked_indices]

        matches: list[tuple[DocumentChunk, float]] = []
        for index, score in zip(ranked_indices, ranked_scores, strict=True):
            if index < 0:
                continue
            matches.append((self.chunks[index], float(score)))
        return matches

    def save(self) -> None:
        if not self.ready:
            return

        metadata = [chunk.model_dump(mode="json") for chunk in self.chunks]
        self.settings.index_metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

        if self.backend == "faiss" and self._index is not None:
            faiss.write_index(self._index, str(self.settings.index_faiss_path))
            if self.settings.index_numpy_path.exists():
                self.settings.index_numpy_path.unlink()
            return

        if self._matrix is not None:
            np.save(self.settings.index_numpy_path, self._matrix)
            if self.settings.index_faiss_path.exists():
                self.settings.index_faiss_path.unlink()

    def load(self) -> bool:
        if not self.settings.index_metadata_path.exists():
            return False

        metadata = json.loads(self.settings.index_metadata_path.read_text(encoding="utf-8"))
        self.chunks = [DocumentChunk.model_validate(item) for item in metadata]

        if self.settings.index_faiss_path.exists() and faiss is not None:
            self._index = faiss.read_index(str(self.settings.index_faiss_path))
            self._matrix = None
            self.dimension = int(self._index.d)
            self.backend = "faiss"
            return True

        if self.settings.index_numpy_path.exists():
            self._matrix = np.load(self.settings.index_numpy_path)
            self._index = None
            self.dimension = int(self._matrix.shape[1])
            self.backend = "numpy"
            return True

        return False

    @staticmethod
    def _normalize(matrix: np.ndarray) -> None:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix /= norms

