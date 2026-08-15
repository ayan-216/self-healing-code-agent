import os
import subprocess
import time
from typing import Dict, Any
from src.agents.state import AuditState
from src.core.config import settings
from src.core.logger import logger


class TestExecutionAgent:
    """
    Agent 7 — Test Execution Agent
    Executes unit tests & integration tests in a sandboxed subprocess environment.
    Captures stdout, stderr, execution time, and exit codes cleanly.
    """

    def run(self, state: AuditState) -> AuditState:
        repo_path = state.get("repo_path", ".")
        logger.info(f"[TestExecutionAgent] Executing tests in sandbox at {repo_path}...")

        start_time = time.time()
        timeout_seconds = settings.SANDBOX_TIMEOUT_SECONDS

        # Determine test framework command (pytest if tests dir exists, otherwise python unittest)
        tests_dir = os.path.join(repo_path, "tests")
        if os.path.exists(tests_dir):
            cmd = ["pytest", repo_path]
        else:
            cmd = ["python", "-m", "unittest", "discover", "-s", repo_path]

        try:
            res = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            duration = time.time() - start_time
            test_results = {
                "success": res.returncode == 0,
                "exit_code": res.returncode,
                "duration_seconds": round(duration, 2),
                "stdout": res.stdout,
                "stderr": res.stderr,
                "timed_out": False
            }
        except subprocess.TimeoutExpired as te:
            duration = time.time() - start_time
            logger.warning(f"[TestExecutionAgent] Test suite timed out after {timeout_seconds} seconds!")
            test_results = {
                "success": False,
                "exit_code": -1,
                "duration_seconds": round(duration, 2),
                "stdout": te.stdout or "",
                "stderr": f"Execution Timed Out after {timeout_seconds}s",
                "timed_out": True
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[TestExecutionAgent] Exception running tests: {e}")
            test_results = {
                "success": False,
                "exit_code": -1,
                "duration_seconds": round(duration, 2),
                "stdout": "",
                "stderr": str(e),
                "timed_out": False
            }

        state["test_results"] = test_results

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "TestExecutionAgent",
            "message": f"Tests executed in {test_results['duration_seconds']}s. Success: {test_results['success']}."
        })
        state["execution_logs"] = logs

        return state
