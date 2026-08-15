import os
from src.graph.workflow import audit_graph


def test_full_autonomous_audit_pipeline(tmp_buggy_repo):
    initial_state = {
        "audit_session_id": "integration-test-session",
        "repo_path": tmp_buggy_repo,
        "repo_name": "test/integration-repo",
        "retry_count": 0,
        "max_retries": 2,
        "execution_logs": []
    }

    final_state = audit_graph.invoke(initial_state)

    assert "issues" in final_state
    assert "validation_status" in final_state
    assert len(final_state["execution_logs"]) >= 6
