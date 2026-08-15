import os
from src.agents.code_analysis import CodeAnalysisAgent


def test_code_analysis_agent(tmp_buggy_repo):
    agent = CodeAnalysisAgent()
    state = {"repo_path": tmp_buggy_repo}
    res_state = agent.run(state)

    assert "issues" in res_state
    assert "dependency_graph" in res_state
    assert "repo_metadata" in res_state
    assert res_state["repo_metadata"]["total_python_files"] >= 2
    assert "calculator.py" in res_state["dependency_graph"]
