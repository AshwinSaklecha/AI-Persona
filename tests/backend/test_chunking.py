from app.models.schemas import SourceDocument
from app.services.chunking import TextChunker


def test_chunker_creates_multiple_overlapping_chunks():
    chunker = TextChunker(chunk_size=180, chunk_overlap=40)
    text = ("Ashwin built backend systems. " * 20) + "\n\n" + ("He also worked on DeepChem. " * 20)
    document = SourceDocument(
        id="resume-1",
        title="Resume",
        text=text,
        source_type="resume",
    )

    chunks = chunker.chunk_document(document)

    assert len(chunks) >= 2
    assert chunks[0].source_title == "Resume"
    assert chunks[1].metadata["start_char"] < chunks[0].metadata["end_char"]

