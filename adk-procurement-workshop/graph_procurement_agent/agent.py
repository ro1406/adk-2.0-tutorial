"""ADK CLI entry point (discovers root_agent for adk web / adk run)."""

from .graph import procurement_workflow

root_agent = procurement_workflow
