import os
from typing import Dict, Any, List
from src.agents.state import AuditState
from src.core.config import settings
from src.core.logger import logger


class PatchGenerationAgent:
    """
    Agent 5 — Patch Generation Agent
    Generates Git-compatible Unified Diffs or file replacements to repair identified issues.
    Preserves coding style and minimizes unnecessary diff noise.
    """

    def run(self, state: AuditState) -> AuditState:
        repair_plan = state.get("repair_plan", {})
        context = state.get("retrieved_context", {})
        reflection = state.get("reflection_notes", "")
        issues = state.get("issues", [])

        logger.info("[PatchGenerationAgent] Generating patch diff...")

        patch_diff = ""

        if settings.USE_MOCK_LLM or not settings.OPENAI_API_KEY:
            # Deterministic patch generation for testing/offline mode
            steps = repair_plan.get("steps", [])
            for step in steps:
                file_path = step.get("file_path")
                file_content = context.get("affected_files_content", {}).get(file_path, "")

                # Simple deterministic fix for common test/syntax errors if file exists
                lines = file_content.splitlines()
                new_lines = []
                for line in lines:
                    # Fix division by zero mock example
                    if "/ 0" in line and not "# fix" in line:
                        new_lines.append(line.replace("/ 0", "/ 1  # fixed by self-healing agent"))
                    # Fix syntax error / undefined variable mock example
                    elif "undefined_var" in line:
                        new_lines.append(line.replace("undefined_var", "'resolved_var'"))
                    else:
                        new_lines.append(line)

                fixed_content = "\n".join(new_lines) + ("\n" if new_lines else "")
                
                # Format as Unified Diff header or full content tag
                patch_diff += f"--- a/{file_path}\n+++ b/{file_path}\n"
                patch_diff += f"FILE_CONTENT_REPLACEMENT:\n{fixed_content}\n"

        else:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.prompts import ChatPromptTemplate

                llm = ChatOpenAI(model=settings.DEFAULT_LLM_MODEL, temperature=0.0)
                
                prompt = ChatPromptTemplate.from_template(
                    "You are a Senior Principal Software Engineer.\n"
                    "Generate a patch fix for the following repository issue.\n\n"
                    "Repair Plan: {repair_plan}\n"
                    "Reflection Notes: {reflection}\n"
                    "Existing File Contents:\n{file_contents}\n\n"
                    "OUTPUT ONLY THE MODIFIED FILE CONTENT FOR EACH FILE IN THIS EXACT FORMAT:\n"
                    "--- a/path/to/file.py\n"
                    "+++ b/path/to/file.py\n"
                    "FILE_CONTENT_REPLACEMENT:\n"
                    "<full modified file content here>\n"
                )

                chain = prompt | llm
                file_contents_str = ""
                for path, content in context.get("affected_files_content", {}).items():
                    file_contents_str += f"=== {path} ===\n{content}\n\n"

                res = chain.invoke({
                    "repair_plan": str(repair_plan),
                    "reflection": reflection,
                    "file_contents": file_contents_str[:4000]
                })

                patch_diff = res.content.strip()
            except Exception as e:
                logger.error(f"[PatchGenerationAgent] LLM patch generation failed: {e}")
                # Fallback
                patch_diff = "--- a/app.py\n+++ b/app.py\nFILE_CONTENT_REPLACEMENT:\n# Patch failed generation\n"

        state["patch_diff"] = patch_diff

        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "PatchGenerationAgent",
            "message": f"Generated patch diff of size {len(patch_diff)} characters."
        })
        state["execution_logs"] = logs

        return state
