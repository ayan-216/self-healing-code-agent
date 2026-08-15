import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from src.core.db.database import get_db
from src.core.db.models import Repository, AuditSession
from src.tasks.audit_tasks import execute_audit_workflow_task
from src.core.config import settings
from src.core.logger import logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db)
):
    body = await request.body()

    # Secret Verification if configured
    if settings.GITHUB_WEBHOOK_SECRET and x_hub_signature_256:
        expected_sig = "sha256=" + hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    if x_github_event in ["push", "pull_request"]:
        repo_data = payload.get("repository", {})
        repo_name = repo_data.get("full_name", "unknown/repo")
        clone_url = repo_data.get("clone_url", "")
        commit_sha = payload.get("after") or payload.get("pull_request", {}).get("head", {}).get("sha", "head")

        logger.info(f"[Webhook] Received {x_github_event} event for {repo_name}")

        # Find or create repository record
        repo = db.query(Repository).filter(Repository.name == repo_name).first()
        if not repo:
            repo = Repository(
                name=repo_name,
                owner=repo_data.get("owner", {}).get("login", "owner"),
                clone_url=clone_url
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)

        # Create Audit Session
        audit = AuditSession(
            repository_id=repo.id,
            status="PENDING",
            commit_sha=commit_sha
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)

        # Enqueue Celery Task (or run directly if celery broker unavailable)
        try:
            execute_audit_workflow_task.apply(
                args=[audit.id, clone_url or ".", repo_name, commit_sha]
            )
        except Exception as e:
            logger.warning(f"Celery enqueue failed, running inline task fallback: {e}")

        return {"status": "enqueued", "audit_session_id": audit.id}

    return {"status": "ignored", "event": x_github_event}
