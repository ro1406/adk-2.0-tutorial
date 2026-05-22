"""Workflow graph edges for the enterprise procurement pipeline."""

from google.adk import Workflow

from .agents import legal_reviewer, security_reviewer
from .routing import (
    complete_procurement,
    execute_purchase,
    hydrate_intake_state,
    manager_hitl,
    notify_rejection,
    route_manager_hitl,
    routing_logic,
    run_intake,
)

procurement_workflow = Workflow(
    name="procurement_workflow",
    edges=[
        ("START", run_intake),
        (run_intake, hydrate_intake_state),
        (hydrate_intake_state, (legal_reviewer, security_reviewer)),
        ((legal_reviewer, security_reviewer), routing_logic),
        (
            routing_logic,
            {
                "reject": notify_rejection,
                "manager": manager_hitl,
                "complete": complete_procurement,
            },
        ),
        (manager_hitl, route_manager_hitl),
        (
            route_manager_hitl,
            {
                "approve": execute_purchase,
                "reject": notify_rejection,
            },
        ),
        (execute_purchase, complete_procurement),
    ],
)
