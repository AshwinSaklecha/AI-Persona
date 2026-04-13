import uuid
from pathlib import Path

from app.core.config import Settings
from app.services.github_source import GitHubSourceService


ROOT_DIR = Path(__file__).resolve().parents[2]


def test_github_source_sync_writes_repo_and_contribution_docs(monkeypatch):
    tmp_path = ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex
    settings = Settings(
        github_username="AshwinSaklecha",
        github_repos="AshwinSaklecha/kv-cache",
        github_contribution_repos="deepchem/deepchem",
        source_dir=tmp_path / "sources",
        index_dir=tmp_path / "indexes",
        log_dir=tmp_path / "logs",
        data_dir=tmp_path,
        _env_file=None,
    )
    settings.github_source_dir.mkdir(parents=True, exist_ok=True)
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    service = GitHubSourceService(settings)

    def fake_get_json(client, path, params=None):
        if path == "/repos/AshwinSaklecha/kv-cache":
            return {
                "html_url": "https://github.com/AshwinSaklecha/kv-cache",
                "default_branch": "main",
                "visibility": "public",
                "stargazers_count": 5,
                "forks_count": 1,
                "description": "KV cache repo",
                "homepage": "",
            }
        if path == "/repos/AshwinSaklecha/kv-cache/languages":
            return {"Python": 1000}
        if path == "/search/issues":
            assert params is not None
            assert params["q"] == "repo:deepchem/deepchem is:pr author:AshwinSaklecha"
            return {
                "items": [
                    {
                        "number": 4661,
                        "title": "Implement DeepONet Architecture",
                    }
                ]
            }
        if path == "/repos/deepchem/deepchem/pulls/4661":
            return {
                "number": 4661,
                "title": "Implement DeepONet Architecture",
                "html_url": "https://github.com/deepchem/deepchem/pull/4661",
                "state": "open",
                "merged_at": None,
                "body": "Adds DeepONet.",
                "user": {"login": "AshwinSaklecha"},
            }
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(service, "_get_json", fake_get_json)
    monkeypatch.setattr(service, "_fetch_readme", lambda client, repo: "# README\n\ncontent")

    result = service.sync(refresh=True)

    assert result.repo_count == 1
    assert result.contribution_repo_count == 1
    assert len(result.generated_files) == 2

    repo_doc = Path(result.generated_files[0]).read_text(encoding="utf-8")
    contribution_doc = Path(result.generated_files[1]).read_text(encoding="utf-8")
    assert "https://github.com/AshwinSaklecha/kv-cache" in repo_doc
    assert "PR #4661" in contribution_doc
