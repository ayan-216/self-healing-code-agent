from langgraph.graph import StateGraph, END
from src.agents.state import AuditState
from src.agents.code_analysis import CodeAnalysisAgent
from src.agents.context_retrieval import ContextRetrievalAgent
from src.agents.root_cause import RootCauseAnalysisAgent
from src.agents.repair_planning import RepairPlanningAgent
from src.agents.patch_generation import PatchGenerationAgent
from src.agents.patch_application import PatchApplicationAgent
from src.agents.test_execution import TestExecutionAgent
from src.agents.validation import ValidationAgent
from src.agents.reflection import ReflectionAgent
from src.agents.memory import MemoryAgent
from src.agents.github_integration import GitHubIntegrationAgent
from src.core.config import settings
from src.core.logger import logger

# initialize agent instances
code_analysis_agent = CodeAnalysisAgent()
context_retrieval_agent = ContextRetrievalAgent()
root_cause_agent = RootCauseAnalysisAgent()
repair_planning_agent = RepairPlanningAgent()
patch_generation_agent = PatchGenerationAgent()
patch_application_agent = PatchApplicationAgent()
test_execution_agent = TestExecutionAgent()
validation_agent = ValidationAgent()
reflection_agent = ReflectionAgent()
memory_agent = MemoryAgent()
github_agent = GitHubIntegrationAgent()


# node wrapper functions
def node_code_analysis(state: AuditState) -> AuditState:
    return code_analysis_agent.run(state)

def node_context_retrieval(state: AuditState) -> AuditState:
    return context_retrieval_agent.run(state)

def node_root_cause(state: AuditState) -> AuditState:
    return root_cause_agent.run(state)

def node_repair_planning(state: AuditState) -> AuditState:
    return repair_planning_agent.run(state)

def node_patch_generation(state: AuditState) -> AuditState:
    return patch_generation_agent.run(state)

def node_patch_application(state: AuditState) -> AuditState:
    return patch_application_agent.run(state)

def node_test_execution(state: AuditState) -> AuditState:
    return test_execution_agent.run(state)

def node_validation(state: AuditState) -> AuditState:
    return validation_agent.run(state)

def node_reflection(state: AuditState) -> AuditState:
    return reflection_agent.run(state)

def node_memory(state: AuditState) -> AuditState:
    return memory_agent.run(state)

def node_github(state: AuditState) -> AuditState:
    return github_agent.run(state)


# conditional router
def route_validation_result(state: AuditState) -> str:
    status = state.get("validation_status", "REJECTED")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", settings.MAX_RETRY_ATTEMPTS)

    if status == "APPROVED":
        logger.info("[LangGraph] Validation PASSED -> Routing to Memory & GitHub Agent")
        return "memory"
    
    if retry_count < max_retries:
        logger.info(f"[LangGraph] Validation FAILED (Attempt {retry_count}/{max_retries}) -> Routing to Reflection Agent")
        return "reflection"
    
    logger.info(f"[LangGraph] Validation FAILED and Max Retries ({max_retries}) Reached -> Routing to Memory Agent")
    return "memory"


def route_post_memory(state: AuditState) -> str:
    status = state.get("validation_status", "REJECTED")
    if status == "APPROVED":
        return "github"
    return END


def create_audit_workflow() -> StateGraph:
    """
    Constructs and compiles the complete 11-agent LangGraph workflow.
    """
    builder = StateGraph(AuditState)

    # 1. register nodes
    builder.add_node("code_analysis", node_code_analysis)
    builder.add_node("context_retrieval", node_context_retrieval)
    builder.add_node("root_cause", node_root_cause)
    builder.add_node("repair_planning", node_repair_planning)
    builder.add_node("patch_generation", node_patch_generation)
    builder.add_node("patch_application", node_patch_application)
    builder.add_node("test_execution", node_test_execution)
    builder.add_node("validation", node_validation)
    builder.add_node("reflection", node_reflection)
    builder.add_node("memory", node_memory)
    builder.add_node("github", node_github)

    # 2. add linear edges
    builder.set_entry_point("code_analysis")
    builder.add_edge("code_analysis", "context_retrieval")
    builder.add_edge("context_retrieval", "root_cause")
    builder.add_edge("root_cause", "repair_planning")
    builder.add_edge("repair_planning", "patch_generation")
    builder.add_edge("patch_generation", "patch_application")
    builder.add_edge("patch_application", "test_execution")
    builder.add_edge("test_execution", "validation")

    # 3. add conditional edge after validation
    builder.add_conditional_edges(
        "validation",
        route_validation_result,
        {
            "approved": "memory",
            "reflection": "reflection",
            "memory": "memory"
        }
    )

    # 4. reflection loops back to repair planning
    builder.add_edge("reflection", "repair_planning")

    # 5. memory routes conditionally to github (if approved) or end (if failed)
    builder.add_conditional_edges(
        "memory",
        route_post_memory,
        {
            "github": "github",
            END: END
        }
    )
    builder.add_edge("github", END)

    return builder.compile()


audit_graph = create_audit_workflow()
