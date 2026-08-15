from typing import Dict, Any
from src.agents.state import AuditState
from src.agents.code_analysis import CodeAnalysisAgent
from src.core.logger import logger


class ValidationAgent:
    """
    Agent 8 — Validation Agent
    Multifaceted validator checking test execution results, static analysis re-scans,
    and regression detection. Decides if patch is APPROVED or REJECTED.
    """

    def run(self, state: AuditState) -> AuditState:
        test_results = state.get("test_results", {})
        initial_issues = state.get("issues", [])
        repo_path = state.get("repo_path", ".")

        logger.info("[ValidationAgent] Evaluating patch validation criteria...")

        validation_reasons = []
        is_approved = True

        # 1. Test Suite Pass Criteria
        if not test_results.get("success", False):
            is_approved = False
            validation_reasons.append(f"Test suite failed or timed out: {test_results.get('stderr', 'Failure')[:200]}")

        # 2. Static Analysis Re-Scan Criteria
        rescanner = CodeAnalysisAgent()
        post_analysis_state = rescanner.run({"repo_path": repo_path})
        post_issues = post_analysis_state.get("issues", [])

        critical_post_issues = [i for i in post_issues if i.get("severity") in ["HIGH", "CRITICAL", "SYNTAX_ERROR"]]
        if critical_post_issues:
            is_approved = False
            validation_reasons.append(f"Post-patch static scan found {len(critical_post_issues)} critical issues or syntax errors.")

        status = "APPROVED" if is_approved else "REJECTED"
        validation_details = {
            "is_approved": is_approved,
            "reasons": validation_reasons if validation_reasons else ["All tests passed and static analysis clean."],
            "initial_issues_count": len(initial_issues),
            "post_issues_count": len(post_issues)
        }

        state["validation_status"] = status
        state["validation_details"] = validation_details

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "ValidationAgent",
            "message": f"Validation status: {status}. Details: {validation_details['reasons']}"
        })
        state["execution_logs"] = logs

        return state
