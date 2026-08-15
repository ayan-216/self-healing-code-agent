from src.agents.test_execution import TestExecutionAgent


def test_test_execution_agent(tmp_buggy_repo):
    agent = TestExecutionAgent()
    state = {"repo_path": tmp_buggy_repo}
    res_state = agent.run(state)

    assert "test_results" in res_state
    results = res_state["test_results"]
    assert "success" in results
    assert "duration_seconds" in results
    # Initially the buggy repo test should fail due to division by zero
    assert results["success"] is False
