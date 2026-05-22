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


#! To do in workshop: Create a workflow object with the name "procurement_workflow"

