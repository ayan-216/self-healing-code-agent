import ast
import os
import shutil
from typing import Dict, Any, List
from src.agents.state import AuditState
from src.core.logger import logger


class PatchApplicationAgent:
    """
    Agent 6 — Patch Application Agent
    Deterministically applies generated patches to disk.
    Creates backups before writing and performs atomic rollback on failure.
    """

    def run(self, state: AuditState) -> AuditState:
        repo_path = state.get("repo_path", ".")
        patch_diff = state.get("patch_diff", "")

        logger.info("[PatchApplicationAgent] Applying patch diff to workspace...")

        if not patch_diff.strip():
            logger.warning("[PatchApplicationAgent] Empty patch diff provided.")
            state["applied_files"] = []
            return state

        backups: Dict[str, str] = state.get("file_backups", {})
        applied_files: List[str] = []

        # Parse custom FILE_CONTENT_REPLACEMENT blocks
        # Format:
        # --- a/path/to/file.py
        # +++ b/path/to/file.py
        # FILE_CONTENT_REPLACEMENT:
        # <content>
        blocks = patch_diff.split("--- a/")
        success = True
        error_msg = ""

        for block in blocks:
            if not block.strip():
                continue

            lines = block.splitlines()
            rel_file = lines[0].strip()
            
            if "FILE_CONTENT_REPLACEMENT:" in block:
                content_start = block.find("FILE_CONTENT_REPLACEMENT:") + len("FILE_CONTENT_REPLACEMENT:\n")
                new_content = block[content_start:]
                
                full_path = os.path.join(repo_path, rel_file)

                # 1. Backup original file content
                if os.path.exists(full_path) and rel_file not in backups:
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            backups[rel_file] = f.read()
                    except Exception as e:
                        logger.warning(f"Could not backup {rel_file}: {e}")

                # 2. Syntax Check new content if Python file
                if rel_file.endswith(".py"):
                    try:
                        ast.parse(new_content, filename=rel_file)
                    except SyntaxError as se:
                        success = False
                        error_msg = f"Patch introduced syntax error in {rel_file} line {se.lineno}: {se.msg}"
                        logger.error(f"[PatchApplicationAgent] {error_msg}")
                        break

                # 3. Write new content
                try:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    applied_files.append(rel_file)
                except Exception as e:
                    success = False
                    error_msg = f"Failed to write file {rel_file}: {e}"
                    logger.error(f"[PatchApplicationAgent] {error_msg}")
                    break

        if not success:
            logger.warning("[PatchApplicationAgent] Rolling back changes due to failure...")
            self.rollback(repo_path, backups)
            applied_files = []
            state["applied_files"] = applied_files
            state["file_backups"] = backups
            
            logs = state.get("execution_logs", [])
            logs.append({
                "agent": "PatchApplicationAgent",
                "message": f"Patch application failed and rolled back. Error: {error_msg}"
            })
            state["execution_logs"] = logs
        else:
            state["applied_files"] = applied_files
            state["file_backups"] = backups

            logs = state.get("execution_logs", [])
            logs.append({
                "agent": "PatchApplicationAgent",
                "message": f"Successfully applied patch to files: {applied_files}"
            })
            state["execution_logs"] = logs

        return state

    def rollback(self, repo_path: str, backups: Dict[str, str]):
        for rel_file, original_content in backups.items():
            full_path = os.path.join(repo_path, rel_file)
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(original_content)
                logger.info(f"[PatchApplicationAgent] Restored backup for {rel_file}")
            except Exception as e:
                logger.error(f"Failed to restore backup for {rel_file}: {e}")
