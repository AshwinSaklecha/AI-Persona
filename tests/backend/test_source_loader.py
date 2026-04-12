from pathlib import Path
import uuid

from app.services.source_loader import LocalSourceLoader


def test_source_loader_extracts_source_url():
    source_dir = Path("tests/backend/.tmp") / uuid.uuid4().hex / "source-loader"
    source_dir.mkdir(parents=True, exist_ok=True)
    sample_path = source_dir / "sample.md"
    sample_path.write_text(
        "# Sample\n\nSource URL: https://github.com/AshwinSaklecha/kv-cache\n\nBody",
        encoding="utf-8",
    )

    loader = LocalSourceLoader(source_dir)
    documents = loader.load()

    assert documents[0].url == "https://github.com/AshwinSaklecha/kv-cache"
