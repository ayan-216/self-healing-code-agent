import time
from datetime import datetime
import os
from src.tasks.celery_app import celery_app
from src.graph.workflow import audit_graph
from src.core.db.database import SessionLocal, init_db
from src.core.db.models import AuditSession, DetectedIssue, RepairAttempt, ExecutionLog, PlatformMetric
from src.core.logger import logger


@celery_app.task(name="execute_audit_workflow_task")
def execute_audit_workflow_task(audit_session_id: str, repo_path: str, repo_name: str, commit_sha: str = None):
    """
    Celery background task that executes the complete 11-agent audit workflow graph.
    """
    logger.info(f"[Celery] Starting audit task for session {audit_session_id}")
    start_time = time.time()

    init_db()
    db = SessionLocal()
    session = db.query(AuditSession).filter(AuditSession.id == audit_session_id).first()
    if session:
        session.status = "RUNNING"
        db.commit()

    # Handle Remote Repository Workspace Caching & Fast Incremental Fetch
    work_dir = repo_path
    if repo_path.startswith("http://") or repo_path.startswith("https://") or repo_path.startswith("git@"):
        import tempfile
        import subprocess
        
        # Create a stable cached directory based on repository name
        safe_repo_folder = repo_name.replace("/", "_").replace("\\", "_")
        cache_base_dir = os.path.join(tempfile.gettempdir(), "ci_agent_cache", safe_repo_folder)
        os.makedirs(cache_base_dir, exist_ok=True)
        
        logger.info(f"[Celery] Syncing repository workspace at {cache_base_dir}...")
        try:
            if not os.path.exists(os.path.join(cache_base_dir, ".git")):
                # First time: Shallow clone with depth 50 for speed
                logger.info(f"[Celery] Performing shallow clone of {repo_path}...")
                subprocess.run(["git", "clone", "--depth", "50", repo_path, cache_base_dir], check=True, capture_output=True, text=True)
            else:
                # Subsequent runs: Fast incremental fetch of new commits only
                logger.info("[Celery] Cache hit! Executing fast git fetch...")
                subprocess.run(["git", "fetch", "--depth", "50", "origin"], cwd=cache_base_dir, check=True, capture_output=True, text=True)
                subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=cache_base_dir, capture_output=True, text=True)

            if commit_sha and commit_sha != "head":
                subprocess.run(["git", "checkout", commit_sha], cwd=cache_base_dir, check=True, capture_output=True, text=True)

            work_dir = cache_base_dir
        except Exception as clone_err:
            logger.error(f"[Celery] Git workspace sync failed: {clone_err}")
            work_dir = repo_path

    initial_state = {
        "audit_session_id": audit_session_id,
        "repo_path": work_dir,
        "repo_name": repo_name,
        "commit_sha": commit_sha,
        "issues": [],
        "dependency_graph": {},
        "repo_metadata": {},
        "file_backups": {},
        "retry_count": 0,
        "max_retries": 3,
        "execution_logs": [],
        "validation_status": "PENDING"
    }
    try:
        final_state = audit_graph.invoke(initial_state)
        duration = time.time() - start_time
        
        val_status = final_state.get("validation_status", "REJECTED")
        pr_url = final_state.get("pr_url")

        if session:
            session.status = "COMPLETED" if val_status == "APPROVED" else "FAILED"
            session.retry_count = final_state.get("retry_count", 0)
            session.pr_url = pr_url
            session.finished_at = datetime.utcnow()

            # Save Detected Issues
            for issue in final_state.get("issues", []):
                db.add(DetectedIssue(
                    audit_session_id=audit_session_id,
                    issue_type=issue.get("issue_type", "BUG"),
                    file_path=issue.get("file_path", "unknown"),
                    line_number=issue.get("line_number"),
                    severity=issue.get("severity", "MEDIUM"),
                    tool=issue.get("tool", "system"),
                    description=issue.get("description", ""),
                    snippet=issue.get("snippet", "")
                ))

            # Save Repair Attempt
            db.add(RepairAttempt(
                audit_session_id=audit_session_id,
                attempt_number=final_state.get("retry_count", 0) + 1,
                root_cause_explanation=str(final_state.get("root_cause", {})),
                repair_plan=final_state.get("repair_plan"),
                patch_diff=final_state.get("patch_diff"),
                validation_status=val_status,
                reflection_notes=final_state.get("reflection_notes")
            ))

            # Save Metric
            db.add(PlatformMetric(
                audit_session_id=audit_session_id,
                execution_time_seconds=round(duration, 2),
                token_usage=final_state.get("token_usage", 0),
                total_cost=0.01,
                validation_passed=(val_status == "APPROVED"),
                retry_count=final_state.get("retry_count", 0)
            ))

            # Save Logs
            for log in final_state.get("execution_logs", []):
                db.add(ExecutionLog(
                    audit_session_id=audit_session_id,
                    agent_name=log.get("agent", "System"),
                    message=log.get("message", "")
                ))

            db.commit()

        logger.info(f"[Celery] Audit session {audit_session_id} finished in {duration:.2f}s with status {val_status}")
        return {"status": val_status, "pr_url": pr_url, "duration": duration}

    except Exception as e:
        logger.error(f"[Celery] Audit session {audit_session_id} failed with error: {e}")
        if session:
            session.status = "FAILED"
            session.finished_at = datetime.utcnow()
            db.commit()
        return {"status": "FAILED", "error": str(e)}
    finally:
        db.close()
