from src.graph.workflow import audit_graph, route_validation_result, route_post_memory
from langgraph.graph import END


def test_graph_routing_approved():
    state = {
        "validation_status": "APPROVED",
        "retry_count": 0,
        "max_retries": 3
    }
    assert route_validation_result(state) == "memory"
    assert route_post_memory(state) == "github"


def test_graph_routing_rejected_with_retries():
    state = {
        "validation_status": "REJECTED",
        "retry_count": 1,
        "max_retries": 3
    }
    assert route_validation_result(state) == "reflection"


def test_graph_routing_rejected_max_retries_reached():
    state = {
        "validation_status": "REJECTED",
        "retry_count": 3,
        "max_retries": 3
    }
    assert route_validation_result(state) == "memory"
    assert route_post_memory(state) == END
