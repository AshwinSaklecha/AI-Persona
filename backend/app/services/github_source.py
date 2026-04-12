from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.core.config import Settings


README_CANDIDATES = ("README.md", "README.MD", "readme.md")


@dataclass(slots=True)
class GitHubSyncResult:
    generated_files: list[str]
    repo_count: int
    contribution_repo_count: int
    synced_at: datetime


class GitHubSourceService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def ready(self) -> bool:
        return bool(self.settings.github_username)

    def sync(
        self,
        repos: list[str] | None = None,
        contribution_repos: list[str] | None = None,
        refresh: bool = True,
    ) -> GitHubSyncResult:
        repo_names = repos or self.settings.github_repo_list
        contribution_repo_names = contribution_repos or self.settings.github_contribution_repo_list
        generated_files: list[str] = []

        self.settings.github_source_dir.mkdir(parents=True, exist_ok=True)

        if refresh:
            for path in self.settings.github_source_dir.glob("*.md"):
                path.unlink()

        with httpx.Client(
            base_url=self.settings.github_api_base_url,
            headers=self._headers(),
            timeout=20.0,
        ) as client:
            for repo_full_name in repo_names:
                payload = self._build_repo_document(client, repo_full_name)
                output_path = self.settings.github_source_dir / f"{self._slug(repo_full_name)}.md"
                output_path.write_text(payload, encoding="utf-8")
                generated_files.append(str(output_path))

            for repo_full_name in contribution_repo_names:
                payload = self._build_contribution_document(client, repo_full_name)
                output_path = self.settings.github_source_dir / f"{self._slug(repo_full_name)}-contributions.md"
                output_path.write_text(payload, encoding="utf-8")
                generated_files.append(str(output_path))

        return GitHubSyncResult(
            generated_files=generated_files,
            repo_count=len(repo_names),
            contribution_repo_count=len(contribution_repo_names),
            synced_at=datetime.now(timezone.utc),
        )

    def _build_repo_document(self, client: httpx.Client, repo_full_name: str) -> str:
        repo = self._get_json(client, f"/repos/{repo_full_name}")
        readme_text = self._fetch_readme(client, repo_full_name) or "README not available."
        languages = self._get_json(client, f"/repos/{repo_full_name}/languages")

        language_summary = ", ".join(sorted(languages.keys())) if languages else "Not available"
        description = repo.get("description") or "No description provided."
        homepage = repo.get("homepage") or ""

        return (
            f"# {repo_full_name}\n\n"
            f"Source URL: {repo.get('html_url')}\n"
            f"Default branch: {repo.get('default_branch')}\n"
            f"Visibility: {repo.get('visibility')}\n"
            f"Stars: {repo.get('stargazers_count')}\n"
            f"Forks: {repo.get('forks_count')}\n"
            f"Primary language summary: {language_summary}\n\n"
            "## Repository Description\n\n"
            f"{description}\n\n"
            f"{'Homepage: ' + homepage + chr(10) + chr(10) if homepage else ''}"
            "## README Snapshot\n\n"
            f"{readme_text.strip()}\n"
        )

    def _build_contribution_document(self, client: httpx.Client, repo_full_name: str) -> str:
        username = self.settings.github_username
        if not username:
            raise RuntimeError("GITHUB_USERNAME is required for contribution ingestion.")

        pulls = self._get_json(
            client,
            f"/repos/{repo_full_name}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
        )
        authored_pulls = [
            pull for pull in pulls if pull.get("user", {}).get("login", "").lower() == username.lower()
        ]

        sections = [
            f"# {repo_full_name} Contributions",
            "",
            f"Source URL: https://github.com/{repo_full_name}",
            f"Contributor: {username}",
            "",
        ]

        if not authored_pulls:
            sections.extend(
                [
                    "No authored pull requests were found from the GitHub API response.",
                    "",
                ]
            )
        else:
            for pull in authored_pulls:
                sections.extend(
                    [
                        f"## PR #{pull['number']} - {pull['title']}",
                        "",
                        f"Pull request URL: {pull['html_url']}",
                        f"State: {pull.get('state')}",
                        f"Merged at: {pull.get('merged_at')}",
                        "",
                        (pull.get("body") or "No PR description provided.").strip(),
                        "",
                    ]
                )

        return "\n".join(sections).strip() + "\n"

    def _fetch_readme(self, client: httpx.Client, repo_full_name: str) -> str | None:
        for candidate in README_CANDIDATES:
            response = client.get(f"/repos/{repo_full_name}/contents/{candidate}")
            if response.status_code == 404:
                continue
            response.raise_for_status()
            payload = response.json()
            if payload.get("encoding") == "base64":
                return base64.b64decode(payload["content"]).decode("utf-8", errors="ignore")
        return None

    @staticmethod
    def _slug(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    @staticmethod
    def _get_json(client: httpx.Client, path: str, params: dict[str, object] | None = None) -> dict | list:
        response = client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ashwin-persona-ingestor",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        return headers

