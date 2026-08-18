# Autonomous Code Audit & Self-Healing Engineering Platform

An enterprise-grade autonomous software engineering platform built with **Python**, **FastAPI**, **LangGraph**, **PostgreSQL**, **Pinecone**, **Redis**, **Celery**, and **Docker**.

The platform autonomously parses software repositories, extracts dependencies, runs static analysis scanners (`flake8`, `bandit`, `ast`), reasons about root causes, formulates structured repair plans, applies atomic file patches with backup rollback safeguards, executes sandboxed test suites, reflects on failure logs, archives long-term memory patterns, and opens automated GitHub Pull Requests.

---

## 🏛 System Architecture & 11-Agent Graph

```
                                  +-------------------------------------------------------+
                                  |                 GitHub Repository / CI                |
                                  +---------------------------+---------------------------+
                                                              | Webhook
                                                              v
                                  +-------------------------------------------------------+
                                  |              FastAPI Webhook & REST API               |
                                  +---------------------------+---------------------------+
                                                              | Dispatch Task
                                                              v
                                  +-------------------------------------------------------+
                                  |              Celery Worker Queue (Redis)              |
                                  +---------------------------+---------------------------+
                                                              | Execute Workflow
                                                              v
                                  +-------------------------------------------------------+
                                  |            LangGraph State Orchestrator               |
                                  +---------------------------+---------------------------+
                                                              |
    +-------------------------+-------------------------------+-------------------------------+-------------------------+
    |                         |                               |                               |                         |
    v                         v                               v                               v                         v
+-------+             +---------------+              +------------------+             +---------------+         +---------------+
| Code  |             | Context RAG   |              | Root Cause       |             | Repair        |         | Patch         |
| Analysis            | Retrieval     |              | Analysis         |             | Planning      |         | Generation    |
| (Flake8, Bandit,    | (Pinecone /   |              | (LLM Reasoning)  |             | (LLM Plan)    |         | (Diff Gen)    |
|  AST, Pylint)       | Vector Store) |              +------------------+             +---------------+         +-------+-------+
+-------+             +---------------+                                                                                |
    |                                                                                                                  v
    |                                                                                                           +---------------+
    |                                                                                                           | Patch         |
    |                                                                                                           | Application   |
    |                                                                                                           | (Backup/Patch)|
    |                                                                                                           +-------+-------+
    |                                                                                                                  |
    |                                                                                                                  v
    |                                                                                                           +---------------+
    |                                                                                                           | Test Execution|
    |                                                                                                           | (Sandboxed)   |
    |                                                                                                           +-------+-------+
    |                                                                                                                  |
    |                                                                                                                  v
    |                                                                                                           +---------------+
    |                                                                                                           | Validation    |
    |                                                                                                           | Agent         |
    |                                                                                                           +-------+-------+
    |                                                                                                                   |
    |                                                   +------------------------------------+--------------------------+
    |                                                   | Validation Passed                  | Validation Failed
    |                                                   v                                    v
    |                                          +------------------+                 +-----------------+
    |                                          | Memory Agent     |                 | Reflection      |
    |                                          | (Store Vector/DB)|                 | Agent           |
    |                                          +--------+---------+                 +--------+--------+
    |                                                   |                                    | (Retry Loop)
    |                                                   v                                    +----+
    |                                          +------------------+                               |
    |                                          | GitHub PR Agent  | <-----------------------------+
    |                                          +------------------+
    v
+-----------------------------------------------------------------------------------------------------------------------+
|                                           Persistence & Observability                                                 |
|                   PostgreSQL (Metadata/Audits)  |  Pinecone (Vectors)  |  LangSmith (Tracing)                      |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## 🤖 The 11 Autonomous Agents

1. **Code Analysis Agent**: Deterministic AST parser (`ast`), dependency graph generator, and static code analyzer (`flake8`, `bandit`).
2. **Context Retrieval Agent**: RAG engine retrieving target file snippets, imported dependencies, and historical repair records.
3. **Root Cause Analysis Agent**: LLM reasoning engine identifying underlying vulnerability or bug origin without emitting code edits.
4. **Repair Planning Agent**: Structured planning engine creating a step-by-step repair strategy targeting specific file spans.
5. **Patch Generation Agent**: Synthesizes minimal Unified Diff format patches respecting code style and syntax rules.
6. **Patch Application Agent**: Deterministic git/file patch applicator featuring file snapshot backups and instant rollback on failure.
7. **Test Execution Agent**: Sandboxed runner managing pytest / unittest suites, returning timed out, pass/fail status, coverage, and full logs.
8. **Validation Agent**: Multi-faceted validator combining static analysis re-scans, test pass criteria, and zero-regression policy.
9. **Reflection Agent**: Failure diagnosis agent analyzing test backtraces & failed diffs to emit actionable retry hints for the repair planner.
10. **Memory Agent**: Indexes successful and failed repair pairs, embedding strategies into Pinecone & PostgreSQL for long-term learning.
11. **GitHub Integration Agent**: Branch manager & GitHub API client for automated PR creation with detailed markdown audit reports.

---

## 🛠 Local Setup & Running Tests

### 1. Requirements
* Python 3.10+
* Docker & Docker Compose (optional for full containerized stack)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Test Suite
To run all unit and integration tests:
```bash
pytest
```

### 4. Run API Server Locally
```bash
uvicorn src.api.main:app --reload --port 8000
```
Interactive API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 5. Launch Full Stack with Docker Compose
```bash
docker-compose up --build
```

---

## 📡 API Endpoints

* `GET /health` — Health check endpoint.
* `POST /api/v1/webhooks/github` — GitHub push & pull request webhook listener.
* `POST /api/v1/audits/trigger` — Manually trigger an audit session.
* `GET /api/v1/audits/{audit_id}` — Fetch audit state, detected issues, repair attempts, and execution logs.
* `GET /api/v1/repositories/` — List all registered repositories.
* `GET /api/v1/metrics/` — Fetch platform evaluation metrics (repair success rate, latency, token usage).

---

## 👤 Author

**Ayan Islam**

