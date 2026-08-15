import uuid
from typing import Dict, Any
from src.agents.state import AuditState
from src.memory.vector_store import vector_store
from src.core.db.database import SessionLocal, init_db
from src.core.db.models import MemoryRecord
from src.core.logger import logger


class MemoryAgent:
    """
    Agent 10 — Memory Agent
    Stores successful and failed repair attempts into PostgreSQL and Pinecone/Vector Store
    for long-term continuous platform learning.
    """

    def run(self, state: AuditState) -> AuditState:
        validation_status = state.get("validation_status", "REJECTED")
        issues = state.get("issues", [])
        patch_diff = state.get("patch_diff", "")
        repo_name = state.get("repo_name", "unknown_repo")

        logger.info(f"[MemoryAgent] Archiving memory record with status {validation_status}...")

        issue_sig = " ".join([i.get("description", "") for i in issues[:3]]) or "general_code_issue"
        record_id = str(uuid.uuid4())

        # 1. Store in Vector Database
        memory_text = (
            f"Repo: {repo_name}\n"
            f"Issue: {issue_sig}\n"
            f"Status: {validation_status}\n"
            f"Patch: {patch_diff[:1000]}\n"
        )
        metadata = {
            "status": validation_status,
            "repo_name": repo_name,
            "issue_signature": issue_sig,
            "retry_count": state.get("retry_count", 0)
        }

        vector_store.store_memory(doc_id=record_id, text=memory_text, metadata=metadata)

        # 2. Store in Relational DB (PostgreSQL / SQLite)
        init_db()
        db = SessionLocal()
        try:
            mem_db_record = MemoryRecord(
                id=record_id,
                issue_signature=issue_sig,
                repository_name=repo_name,
                repair_pattern=patch_diff[:4000],
                status=validation_status,
                vector_id=record_id,
                metadata_json=metadata
            )
            db.add(mem_db_record)
            db.commit()
            logger.info(f"[MemoryAgent] Stored memory record {record_id} in relational database.")
        except Exception as e:
            db.rollback()
            logger.error(f"[MemoryAgent] Error saving memory to database: {e}")
        finally:
            db.close()

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "MemoryAgent",
            "message": f"Memory archived under ID {record_id}."
        })
        state["execution_logs"] = logs

        return state
