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

#! To do in workshop: Create procurement_workflow with edges (see reference graph.py):
#!   START → run_intake → hydrate → (legal, security) → routing_logic
#!   routing_logic → reject | manager_hitl | complete
#!   manager_hitl → route_manager_hitl → approve: execute_purchase | reject: notify_rejection
#!   execute_purchase → complete_procurement
