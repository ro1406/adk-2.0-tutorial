"""ADK CLI entry point — root is a coordinator Agent, not a Workflow."""

from .agents import procurement_coordinator

root_agent = procurement_coordinator
