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
    monkeypatch.setattr(service, "_fetch_nested_readmes", lambda client, repo: "")

    result = service.sync(refresh=True)

    assert result.repo_count == 1
    assert result.contribution_repo_count == 1
    assert len(result.generated_files) == 2

    repo_doc = Path(result.generated_files[0]).read_text(encoding="utf-8")
    contribution_doc = Path(result.generated_files[1]).read_text(encoding="utf-8")
    assert "https://github.com/AshwinSaklecha/kv-cache" in repo_doc
    assert "PR #4661" in contribution_doc


def test_fetch_readme_uses_repo_readme_endpoint_before_filename_guesses():
    service = GitHubSourceService(
        Settings(
            github_username="AshwinSaklecha",
            source_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "sources",
            index_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "indexes",
            log_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "logs",
            data_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex,
            _env_file=None,
        )
    )

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise AssertionError("response should not raise")

        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self):
            self.paths = []

        def get(self, path):
            self.paths.append(path)
            if path == "/repos/AshwinSaklecha/smart-doc-generator/readme":
                return FakeResponse(
                    200,
                    {
                        "encoding": "base64",
                        "content": "IyBSRUFETUUKCnNtYXJ0LWRvYy1nZW5lcmF0b3I=",
                    },
                )
            return FakeResponse(404, {})

    client = FakeClient()

    readme = service._fetch_readme(client, "AshwinSaklecha/smart-doc-generator")

    assert readme == "# README\n\nsmart-doc-generator"
    assert client.paths == ["/repos/AshwinSaklecha/smart-doc-generator/readme"]


def test_fetch_nested_readmes_collects_frontend_and_backend_docs():
    service = GitHubSourceService(
        Settings(
            github_username="AshwinSaklecha",
            source_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "sources",
            index_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "indexes",
            log_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "logs",
            data_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex,
            _env_file=None,
        )
    )

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise AssertionError("response should not raise")

        def json(self):
            return self._payload

    class FakeClient:
        def get(self, path):
            payloads = {
                "/repos/AshwinSaklecha/eCommerce-App/contents/frontend/README.md": {
                    "encoding": "base64",
                    "content": "IyBGcm9udGVuZAoKUmVhZG1l",
                },
                "/repos/AshwinSaklecha/eCommerce-App/contents/backend/README.md": {
                    "encoding": "base64",
                    "content": "IyBCYWNrZW5kCgpSZWFkbWU=",
                },
            }
            if path in payloads:
                return FakeResponse(200, payloads[path])
            return FakeResponse(404, {})

    nested = service._fetch_nested_readmes(FakeClient(), "AshwinSaklecha/eCommerce-App")

    assert "Additional README: frontend" in nested
    assert "Additional README: backend" in nested


def test_fetch_nested_readmes_skips_cra_boilerplate():
    service = GitHubSourceService(
        Settings(
            github_username="AshwinSaklecha",
            source_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "sources",
            index_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "indexes",
            log_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex / "logs",
            data_dir=ROOT_DIR / "tests" / "backend" / ".tmp" / uuid.uuid4().hex,
            _env_file=None,
        )
    )

    assert service._is_boilerplate_readme(
        "# Getting Started with Create React App\n\n"
        "This project was bootstrapped with Create React App.\n\n"
        "## Available Scripts\n\n"
        "## Learn React\n"
    )
