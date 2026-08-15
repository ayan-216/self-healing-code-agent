from typing import Dict, Any, List
from pydantic import BaseModel, Field
from src.agents.state import AuditState
from src.core.config import settings
from src.core.logger import logger


class RepairStep(BaseModel):
    file_path: str = Field(description="File to modify")
    action: str = Field(description="Description of action: e.g. Fix syntax, add check, refactor function")


class RepairPlanOutput(BaseModel):
    steps: List[RepairStep] = Field(description="Ordered list of modification steps")
    required_tests: List[str] = Field(description="Names or commands of unit tests required for verification")
    validation_strategy: str = Field(description="How success will be validated")


class RepairPlanningAgent:
    """
    Agent 4 — Repair Planning Agent
    Generates a structured, multi-step repair plan before any code generation occurs.
    """

    def run(self, state: AuditState) -> AuditState:
        root_cause = state.get("root_cause", {})
        issues = state.get("issues", [])
        reflection = state.get("reflection_notes", "")

        logger.info("[RepairPlanningAgent] Formulating repair plan...")

        if settings.USE_MOCK_LLM or not settings.OPENAI_API_KEY:
            # Deterministic planning fallback
            steps = []
            affected_files = root_cause.get("affected_components", [])
            if not affected_files and issues:
                affected_files = [issues[0].get("file_path", "main.py")]

            for f in affected_files:
                steps.append({
                    "file_path": f,
                    "action": f"Apply fix for root cause: {root_cause.get('explanation', 'Issue repair')}"
                })

            plan = {
                "steps": steps,
                "required_tests": ["pytest"],
                "validation_strategy": "Re-run static analysis (flake8/bandit) and execute pytest suite."
            }
        else:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate

                llm = ChatOpenAI(model=settings.DEFAULT_LLM_MODEL, temperature=0.1)
                structured_llm = llm.with_structured_output(RepairPlanOutput)

                prompt = ChatPromptTemplate.from_template(
                    "You are an Expert Software Architect.\n"
                    "Based on the following root cause explanation and previous reflection notes (if any),\n"
                    "create a concise, step-by-step repair plan.\n\n"
                    "Root Cause: {root_cause}\n"
                    "Reflection Notes: {reflection}\n"
                    "Issues: {issues}\n"
                )

                chain = prompt | structured_llm
                res: RepairPlanOutput = chain.invoke({
                    "root_cause": root_cause.get("explanation", ""),
                    "reflection": reflection,
                    "issues": str(issues)
                })

                plan = res.model_dump()
            except Exception as e:
                logger.error(f"[RepairPlanningAgent] LLM plan generation failed: {e}")
                plan = {
                    "steps": [{"file_path": issues[0].get("file_path", "app.py"), "action": "Fix issue"}],
                    "required_tests": ["pytest"],
                    "validation_strategy": "Run static scanners and test suite."
                }

        state["repair_plan"] = plan

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "RepairPlanningAgent",
            "message": f"Planned {len(plan['steps'])} repair steps targeting files: {[s['file_path'] for s in plan['steps']]}"
        })
        state["execution_logs"] = logs

        return state
