from typing import Dict, Any
from src.agents.state import AuditState
from src.core.config import settings
from src.core.logger import logger


class ReflectionAgent:
    """
    Agent 9 — Reflection Agent
    Analyzes failed repair attempts by evaluating test failure logs, static scan output,
    and previous patch diffs. Emits actionable reflection notes for intelligent retries.
    """

    def run(self, state: AuditState) -> AuditState:
        validation_details = state.get("validation_details", {})
        test_results = state.get("test_results", {})
        patch_diff = state.get("patch_diff", "")
        retry_count = state.get("retry_count", 0) + 1

        logger.info(f"[ReflectionAgent] Analyzing failed attempt #{retry_count}...")

        reasons = validation_details.get("reasons", ["Unknown failure"])
        stderr = test_results.get("stderr", "")
        stdout = test_results.get("stdout", "")

        if settings.USE_MOCK_LLM or not settings.OPENAI_API_KEY:
            reflection_notes = (
                f"Attempt #{retry_count} failed.\n"
                f"Validation Reasons: {reasons}\n"
                f"Test Output: {stderr or stdout}\n"
                f"Strategy: Avoid previous invalid syntax or broken logic in diff."
            )
        else:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate

                llm = ChatOpenAI(model=settings.DEFAULT_LLM_MODEL, temperature=0.2)
                prompt = ChatPromptTemplate.from_template(
                    "You are a Senior Debugging & Reflection Agent.\n"
                    "The previous repair attempt failed validation.\n"
                    "Analyze the failure details and suggest specific corrections for the next repair plan.\n\n"
                    "Validation Reasons: {reasons}\n"
                    "Test Stderr/Stdout: {test_output}\n"
                    "Previous Patch Diff: {patch_diff}\n"
                )

                chain = prompt | llm
                res = chain.invoke({
                    "reasons": str(reasons),
                    "test_output": (stderr + "\n" + stdout)[:2000],
                    "patch_diff": patch_diff[:2000]
                })

                reflection_notes = res.content.strip()
            except Exception as e:
                logger.error(f"[ReflectionAgent] Reflection LLM failed: {e}")
                reflection_notes = f"Reflection failure notes: {reasons}"

        state["reflection_notes"] = reflection_notes
        state["retry_count"] = retry_count

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "ReflectionAgent",
            "message": f"Reflection note created for attempt #{retry_count}: {reflection_notes[:100]}..."
        })
        state["execution_logs"] = logs

        return state
