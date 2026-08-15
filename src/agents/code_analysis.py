import ast
import os
import subprocess
from typing import Dict, Any, List
from src.agents.state import AuditState
from src.core.logger import logger


class CodeAnalysisAgent:
    """
    Agent 1 — Code Analysis Agent
    Deterministic agent that parses repository AST, extracts dependency graphs,
    runs linters and security scanners, and collects repo metadata.
    """

    def run(self, state: AuditState) -> AuditState:
        repo_path = state.get("repo_path", ".")
        logger.info(f"[CodeAnalysisAgent] Analyzing repository at {repo_path}")

        issues: List[Dict[str, Any]] = []
        dependency_graph: Dict[str, List[str]] = {}
        file_list: List[str] = []

        # 1. AST Parsing & Dependency Extraction
        total_files = 0
        total_lines = 0

        for root, _, files in os.walk(repo_path):
            # Exclude virtual environments, git, cache
            if any(p in root for p in [".git", "__pycache__", ".venv", "venv", ".pytest_cache"]):
                continue

            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    file_list.append(rel_path)
                    total_files += 1

                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            lines = content.splitlines()
                            total_lines += len(lines)

                        # Parse AST
                        tree = ast.parse(content, filename=rel_path)
                        imports = self._extract_imports(tree)
                        dependency_graph[rel_path] = imports

                    except SyntaxError as e:
                        issues.append({
                            "issue_type": "SYNTAX_ERROR",
                            "file_path": rel_path,
                            "line_number": e.lineno or 1,
                            "severity": "CRITICAL",
                            "tool": "ast",
                            "description": f"Syntax Error: {e.msg}",
                            "snippet": e.text.strip() if e.text else ""
                        })
                    except Exception as e:
                        logger.warning(f"Error reading/parsing file {rel_path}: {e}")

        # 2. Run Flake8 Linter
        flake8_issues = self._run_flake8(repo_path)
        issues.extend(flake8_issues)

        # 3. Run Bandit Security Scanner
        bandit_issues = self._run_bandit(repo_path)
        issues.extend(bandit_issues)

        repo_metadata = {
            "total_python_files": total_files,
            "total_lines_of_code": total_lines,
            "detected_issues_count": len(issues),
            "files": file_list
        }

        # Update state
        state["issues"] = issues
        state["dependency_graph"] = dependency_graph
        state["repo_metadata"] = repo_metadata
        
        logs = state.get("execution_logs", [])
        logs.append({
            "agent": "CodeAnalysisAgent",
            "message": f"Analysis complete. Found {len(issues)} issues across {total_files} files."
        })
        state["execution_logs"] = logs

        return state

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return list(set(imports))

    def _run_flake8(self, repo_path: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            res = subprocess.run(
                ["flake8", "--max-line-length=120", repo_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            for line in res.stdout.splitlines():
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    raw_file, line_num, col_num, msg = parts[0], parts[1], parts[2], parts[3]
                    rel_file = os.path.relpath(raw_file, repo_path)
                    issues.append({
                        "issue_type": "LINT",
                        "file_path": rel_file,
                        "line_number": int(line_num) if line_num.isdigit() else 1,
                        "severity": "LOW",
                        "tool": "flake8",
                        "description": msg.strip(),
                        "snippet": ""
                    })
        except Exception as e:
            logger.info(f"[CodeAnalysisAgent] Flake8 run skipped/failed: {e}")
        return issues

    def _run_bandit(self, repo_path: str) -> List[Dict[str, Any]]:
        issues = []
        try:
            res = subprocess.run(
                ["bandit", "-r", "-f", "csv", repo_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Skip CSV header line if present
            lines = res.stdout.splitlines()
            for line in lines:
                if "filename" in line or not line.strip():
                    continue
                parts = line.split(",")
                if len(parts) >= 7:
                    file_p, line_n, issue_text, severity = parts[0], parts[1], parts[4], parts[6]
                    rel_file = os.path.relpath(file_p, repo_path)
                    issues.append({
                        "issue_type": "SECURITY",
                        "file_path": rel_file,
                        "line_number": int(line_n) if line_n.isdigit() else 1,
                        "severity": severity.strip().upper(),
                        "tool": "bandit",
                        "description": issue_text.strip(),
                        "snippet": ""
                    })
        except Exception as e:
            logger.info(f"[CodeAnalysisAgent] Bandit run skipped/failed: {e}")
        return issues









