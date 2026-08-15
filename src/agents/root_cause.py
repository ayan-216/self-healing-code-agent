from typing import Dict, Any, List
from pydantic import BaseModel, Field
from src.agents.state import AuditState
from src.core.config import settings
from src.core.logger import logger


class RootCauseOutput(BaseModel):
    explanation: str = Field(description="Detailed explanation of why the issue exists")
    affected_components: List[str] = Field(description="Files and functions impacted")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")


class RootCauseAnalysisAgent:
    """
    Agent 3 — Root Cause Analysis Agent
    Explains why an issue exists without generating any code.
    Only produces structured reasoning.
    """

    def run(self, state: AuditState) -> AuditState:
        issues = state.get("issues", [])
        context = state.get("retrieved_context", {})
        reflection = state.get("reflection_notes", "")

        logger.info(f"[RootCauseAnalysisAgent] Reasoning about root cause for {len(issues)} issues...")

        if not issues:
            state["root_cause"] = {
                "explanation": "No issues were detected in code analysis.",
                "affected_components": [],
                "confidence_score": 1.0
            }
            return state

        if settings.USE_MOCK_LLM or not settings.OPENAI_API_KEY:
            # Deterministic reasoning fallback
            first_issue = issues[0]
            affected_file = first_issue.get("file_path", "unknown")
            desc = first_issue.get("description", "Unknown error")
            
            explanation = f"Root cause stems from issue ({first_issue.get('issue_type')}) in {affected_file}: {desc}."
            if reflection:
                explanation += f" Previous repair failed with reflection: {reflection}"

            root_cause = {
                "explanation": explanation,
                "affected_components": [affected_file],
                "confidence_score": 0.95
            }
        else:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate

                llm = ChatOpenAI(model=settings.DEFAULT_LLM_MODEL, temperature=0.1)
                structured_llm = llm.with_structured_output(RootCauseOutput)

                prompt = ChatPromptTemplate.from_template(
                    "You are a Senior Security Architect and Root Cause Analysis Engine.\n"
                    "Analyze the following static analysis issues, code context, and reflection notes.\n"
                    "Deduce WHY the bug/vulnerability exists.\n\n"
                    "DO NOT GENERATE ANY CODE OR FIXES. ONLY REASON ABOUT THE ROOT CAUSE.\n\n"
                    "Issues: {issues}\n"
                    "Reflection Notes: {reflection}\n"
                    "Code Snippets: {snippets}\n"
                )

                chain = prompt | structured_llm
                snippets_summary = str(context.get("affected_files_content", {}))[:3000]

                res: RootCauseOutput = chain.invoke({
                    "issues": str(issues),
                    "reflection": reflection,
                    "snippets": snippets_summary
                })

                root_cause = res.model_dump()
            except Exception as e:
                logger.error(f"[RootCauseAnalysisAgent] LLM reasoning failed, fallback to mock: {e}")
                root_cause = {
                    "explanation": f"Root cause analysis based on issues: {issues[0].get('description')}",
                    "affected_components": [issues[0].get("file_path", "")],
                    "confidence_score": 0.8
                }

        state["root_cause"] = root_cause

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "RootCauseAnalysisAgent",
            "message": f"Root cause determined with confidence {root_cause['confidence_score']}: {root_cause['explanation'][:100]}..."
        })
        state["execution_logs"] = logs

        return state
