"""Minimal workflow shell: one edge into the Python orchestrator."""

from google.adk import Workflow

from .orchestrator import procurement_orchestrator

procurement_workflow = Workflow(
    name="dynamic_procurement_workflow",
    edges=[("START", procurement_orchestrator)],
)
