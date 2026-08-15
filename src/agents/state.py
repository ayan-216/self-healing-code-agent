from typing import TypedDict, List, Dict, Any, Optional


class AuditState(TypedDict, total=False):
    audit_session_id: str
    repo_path: str
    repo_name: str
    commit_sha: Optional[str]
    
    # Analysis outputs
    issues: List[Dict[str, Any]]
    dependency_graph: Dict[str, Any]
    repo_metadata: Dict[str, Any]
    
    # Context Retrieval outputs
    retrieved_context: Dict[str, Any]
    
    # Reasoning outputs
    root_cause: Optional[Dict[str, Any]]
    repair_plan: Optional[Dict[str, Any]]
    
    # Patch & Application outputs
    patch_diff: Optional[str]
    applied_files: List[str]
    file_backups: Dict[str, str]
    
    # Test & Validation outputs
    test_results: Optional[Dict[str, Any]]
    validation_status: str  # PENDING, APPROVED, REJECTED
    validation_details: Optional[Dict[str, Any]]
    
    # Reflection & Retry outputs
    reflection_notes: Optional[str]
    retry_count: int
    max_retries: int
    
    # PR Integration output
    pr_url: Optional[str]
    
    # Metrics & Observability
    token_usage: int
    execution_logs: List[Dict[str, Any]]
