import os
from typing import Dict, Any, List
from src.agents.state import AuditState
from src.memory.vector_store import vector_store
from src.core.logger import logger


class ContextRetrievalAgent:
    """
    Agent 2 — Context Retrieval Agent (RAG Layer)
    Retrieves only the information required for solving detected issues:
    - Target file snippets
    - Dependent file signatures
    - Historical repair memories from vector store
    """

    def run(self, state: AuditState) -> AuditState:
        repo_path = state.get("repo_path", ".")
        issues = state.get("issues", [])
        dep_graph = state.get("dependency_graph", {})

        logger.info(f"[ContextRetrievalAgent] Retrieving context for {len(issues)} detected issues...")

        file_snippets: Dict[str, str] = {}
        historical_repairs: List[Dict[str, Any]] = []

        # 1. Fetch file content for affected files
        affected_files = set(issue["file_path"] for issue in issues if "file_path" in issue)
        for rel_file in affected_files:
            full_path = os.path.join(repo_path, rel_file)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_snippets[rel_file] = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read affected file {rel_file}: {e}")

        # 2. Retrieve Historical Fix Memories via RAG
        query_signature = " ".join([i.get("description", "") for i in issues[:5]])
        if query_signature.strip():
            similar_records = vector_store.search_similar_repairs(query_signature, top_k=3)
            historical_repairs = similar_records

        retrieved_context = {
            "affected_files_content": file_snippets,
            "dependency_graph": dep_graph,
            "historical_repairs": historical_repairs
        }

        state["retrieved_context"] = retrieved_context

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "ContextRetrievalAgent",
            "message": f"Retrieved content for {len(file_snippets)} files and {len(historical_repairs)} historical repair patterns."
        })
        state["execution_logs"] = logs

        return state
