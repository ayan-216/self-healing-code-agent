from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from src.core.db.database import get_db
from src.core.db.models import AuditSession, Repository, DetectedIssue, RepairAttempt, ExecutionLog
from src.tasks.audit_tasks import execute_audit_workflow_task

router = APIRouter(prefix="/audits", tags=["audits"])


class TriggerAuditRequest(BaseModel):
    repo_path: str = "."
    repo_name: str = "local/repo"
    commit_sha: Optional[str] = None


@router.post("/trigger")
def trigger_audit(req: TriggerAuditRequest, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.name == req.repo_name).first()
    if not repo:
        repo = Repository(
            name=req.repo_name,
            owner="local",
            clone_url=req.repo_path
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

    session = AuditSession(
        repository_id=repo.id,
        status="PENDING",
        commit_sha=req.commit_sha
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        execute_audit_workflow_task.apply(
            args=[session.id, req.repo_path, req.repo_name, req.commit_sha]
        )
    except Exception as e:
        logger.warning(f"Celery dispatch failed: {e}")

    return {"audit_session_id": session.id, "status": "PENDING"}


@router.get("/{audit_id}")
def get_audit(audit_id: str, db: Session = Depends(get_db)):
    session = db.query(AuditSession).filter(AuditSession.id == audit_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")

    issues = db.query(DetectedIssue).filter(DetectedIssue.audit_session_id == audit_id).all()
    attempts = db.query(RepairAttempt).filter(RepairAttempt.audit_session_id == audit_id).all()
    logs = db.query(ExecutionLog).filter(ExecutionLog.audit_session_id == audit_id).all()

    return {
        "id": session.id,
        "repository_id": session.repository_id,
        "status": session.status,
        "retry_count": session.retry_count,
        "pr_url": session.pr_url,
        "created_at": session.created_at,
        "finished_at": session.finished_at,
        "detected_issues": [
            {
                "issue_type": i.issue_type,
                "file_path": i.file_path,
                "line_number": i.line_number,
                "severity": i.severity,
                "description": i.description
            } for i in issues
        ],
        "repair_attempts": [
            {
                "attempt_number": a.attempt_number,
                "validation_status": a.validation_status,
                "patch_diff": a.patch_diff,
                "reflection_notes": a.reflection_notes
            } for a in attempts
        ],
        "logs": [
            {"agent": l.agent_name, "message": l.message, "created_at": l.created_at} for l in logs
        ]
    }
