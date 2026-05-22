"""Workflow graph edges for the enterprise procurement pipeline."""

from google.adk import Workflow

from .agents import legal_reviewer, manager_override, security_reviewer
from .routing import (
    complete_procurement,
    hydrate_intake_state,
    notify_rejection,
    route_after_manager,
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
                "manager": manager_override,
                "complete": complete_procurement,
            },
        ),
        (manager_override, route_after_manager),
        (
            route_after_manager,
            {
                "complete": complete_procurement,
                "reject": notify_rejection,
            },
        ),
    ],
)
