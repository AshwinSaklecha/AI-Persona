import shutil
import uuid
from pathlib import Path

from app.core.config import Settings
from app.models.schemas import DocumentChunk
from app.services.vector_store import VectorStore


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_vector_store_rebuild_and_search():
    tmp_path = ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex
    settings = Settings(
        index_dir=tmp_path / "indexes",
        log_dir=tmp_path / "logs",
        source_dir=tmp_path / "sources",
        data_dir=tmp_path,
    )
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.source_dir.mkdir(parents=True, exist_ok=True)

    store = VectorStore(settings)
    chunks = [
        DocumentChunk(
            id="1",
            source_id="resume",
            source_title="Resume",
            source_type="resume",
            text="Backend and FastAPI experience",
            chunk_index=0,
        ),
        DocumentChunk(
            id="2",
            source_id="project",
            source_title="KV Cache",
            source_type="github",
            text="LRU eviction and asyncio server",
            chunk_index=0,
        ),
    ]
    embeddings = [[1.0, 0.0], [0.0, 1.0]]

    store.rebuild(chunks, embeddings)
    matches = store.search([1.0, 0.0], top_k=1)

    assert matches[0][0].source_title == "Resume"
    assert matches[0][1] > 0.99

    shutil.rmtree(tmp_path, ignore_errors=True)
