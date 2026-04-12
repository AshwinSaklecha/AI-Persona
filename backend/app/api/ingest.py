from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_services
from app.models.schemas import GitHubIngestRequest, GitHubIngestResponse, IngestResponse
from app.services.container import ServiceContainer


router = APIRouter(tags=["ingest"])


@router.post("/ingest/rebuild", response_model=IngestResponse)
def rebuild_index(services: ServiceContainer = Depends(get_services)) -> IngestResponse:
    if not services.embeddings.ready:
        raise HTTPException(status_code=503, detail="Gemini embeddings are not configured.")
    return services.rebuild_index()


@router.post("/ingest/github", response_model=GitHubIngestResponse)
def sync_github_sources(
    request: GitHubIngestRequest,
    services: ServiceContainer = Depends(get_services),
) -> GitHubIngestResponse:
    if not services.github_source.ready:
        raise HTTPException(status_code=503, detail="GitHub source ingestion is not configured.")

    try:
        result = services.github_source.sync(
            repos=request.repos,
            contribution_repos=request.contribution_repos,
            refresh=request.refresh,
        )
    except Exception as exc:
        services.evaluation.log_failure("github_sync_failed", {"error": str(exc)})
        raise HTTPException(status_code=503, detail="GitHub sync failed.") from exc

    rebuilt = None
    if request.rebuild_index:
        if not services.embeddings.ready:
            raise HTTPException(
                status_code=503,
                detail="GitHub sync succeeded, but Gemini embeddings are not configured for reindexing.",
            )
        rebuilt = services.rebuild_index()

    return GitHubIngestResponse(
        generated_files=result.generated_files,
        repo_count=result.repo_count,
        contribution_repo_count=result.contribution_repo_count,
        index_rebuilt=rebuilt is not None,
        document_count=rebuilt.document_count if rebuilt else None,
        chunk_count=rebuilt.chunk_count if rebuilt else None,
        synced_at=result.synced_at,
    )
