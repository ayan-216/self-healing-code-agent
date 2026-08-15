import os
from src.agents.patch_application import PatchApplicationAgent


def test_patch_application_and_backup(tmp_buggy_repo):
    agent = PatchApplicationAgent()
    
    patch_diff = (
        "--- a/calculator.py\n"
        "+++ b/calculator.py\n"
        "FILE_CONTENT_REPLACEMENT:\n"
        "def compute_ratio(a, b):\n"
        "    return a / b\n"
    )

    state = {
        "repo_path": tmp_buggy_repo,
        "patch_diff": patch_diff,
        "file_backups": {}
    }

    res_state = agent.run(state)
    assert "calculator.py" in res_state.get("applied_files", [])
    assert "calculator.py" in res_state.get("file_backups", {})

    # Check updated file content
    calc_path = os.path.join(tmp_buggy_repo, "calculator.py")
    with open(calc_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "return a / b" in content


def test_patch_rollback_on_syntax_error(tmp_buggy_repo):
    agent = PatchApplicationAgent()
    
    # Invalid syntax patch
    bad_patch = (
        "--- a/calculator.py\n"
        "+++ b/calculator.py\n"
        "FILE_CONTENT_REPLACEMENT:\n"
        "def compute_ratio(a, b\n"  # missing parenthesis
    )

    state = {
        "repo_path": tmp_buggy_repo,
        "patch_diff": bad_patch,
        "file_backups": {}
    }

    res_state = agent.run(state)
    assert res_state.get("applied_files") == []

    # Verify original file preserved
    calc_path = os.path.join(tmp_buggy_repo, "calculator.py")
    with open(calc_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "return a / 0" in content
