from src.agents.context_retrieval import ContextRetrievalAgent
from src.agents.root_cause import RootCauseAnalysisAgent
from src.agents.repair_planning import RepairPlanningAgent
from src.agents.reflection import ReflectionAgent
from src.agents.memory import MemoryAgent
from src.agents.github_integration import GitHubIntegrationAgent


def test_agents_flow_units(tmp_buggy_repo):
    state = {
        "repo_path": tmp_buggy_repo,
        "repo_name": "test/repo",
        "issues": [{"issue_type": "BUG", "file_path": "calculator.py", "description": "Division by zero"}],
        "dependency_graph": {"calculator.py": []},
        "retry_count": 0,
        "max_retries": 3
    }

    # 1. Context Retrieval
    ctx_agent = ContextRetrievalAgent()
    state = ctx_agent.run(state)
    assert "retrieved_context" in state
    assert "calculator.py" in state["retrieved_context"]["affected_files_content"]

    # 2. Root Cause
    rc_agent = RootCauseAnalysisAgent()
    state = rc_agent.run(state)
    assert "root_cause" in state
    assert state["root_cause"]["confidence_score"] > 0

    # 3. Repair Planning
    rp_agent = RepairPlanningAgent()
    state = rp_agent.run(state)
    assert "repair_plan" in state
    assert len(state["repair_plan"]["steps"]) > 0

    # 4. Reflection Agent
    ref_agent = ReflectionAgent()
    state["validation_details"] = {"reasons": ["Test ratio failed with ZeroDivisionError"]}
    state["test_results"] = {"stderr": "ZeroDivisionError: division by zero", "stdout": ""}
    state = ref_agent.run(state)
    assert state["retry_count"] == 1
    assert "Attempt #1 failed" in state["reflection_notes"]

    # 5. Memory Agent
    mem_agent = MemoryAgent()
    state["validation_status"] = "APPROVED"
    state["patch_diff"] = "--- a/calculator.py\n+++ b/calculator.py\nFILE_CONTENT_REPLACEMENT:\ndef compute_ratio(a, b):\n return a / b\n"
    state = mem_agent.run(state)
    assert len(state.get("execution_logs", [])) > 0

    # 6. GitHub Integration Agent
    gh_agent = GitHubIntegrationAgent()
    state = gh_agent.run(state)
    assert state["pr_url"] is not None
