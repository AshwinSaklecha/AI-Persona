from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import DocumentChunk, SourceDocument


@dataclass(slots=True)
class TextChunker:
    chunk_size: int
    chunk_overlap: int

    def chunk_documents(self, documents: list[SourceDocument]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for document in documents:
            chunks.extend(self.chunk_document(document))
        return chunks

    def chunk_document(self, document: SourceDocument) -> list[DocumentChunk]:
        text = document.text.strip()
        if not text:
            return []

        chunks: list[DocumentChunk] = []
        start = 0
        chunk_index = 0
        length = len(text)

        while start < length:
            end = min(start + self.chunk_size, length)
            if end < length:
                breakpoint = text.rfind("\n\n", start, end)
                if breakpoint == -1:
                    breakpoint = text.rfind(". ", start, end)
                if breakpoint > start + int(self.chunk_size * 0.6):
                    end = breakpoint + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        id=f"{document.id}::{chunk_index}",
                        source_id=document.id,
                        source_title=document.title,
                        source_type=document.source_type,
                        text=chunk_text,
                        url=document.url,
                        chunk_index=chunk_index,
                        metadata={
                            **document.metadata,
                            "start_char": start,
                            "end_char": end,
                        },
                    )
                )
                chunk_index += 1

            if end >= length:
                break

            start = max(end - self.chunk_overlap, 0)

        return chunks

