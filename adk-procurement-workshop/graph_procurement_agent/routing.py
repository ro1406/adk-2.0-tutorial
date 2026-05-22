"""Routing nodes and task-intake bridge for the graph workflow."""

from google.adk import Context, Event
from google.adk.workflow import node

from .agents import intake_specialist
from .db import MockSQLiteSessionService
from .schemas import ProcurementForm

db = MockSQLiteSessionService()


@node(rerun_on_resume=True, name="run_intake")
async def run_intake(ctx: Context, node_input) -> dict:
    """Dispatch task-mode intake via ctx.run_node (required in ADK 2.0 GA).

    mode='task' agents cannot sit on static Workflow edges. See ADK validation:
    use a chat coordinator with task sub-agents, or ctx.run_node from a node.
    """
    result = await ctx.run_node(intake_specialist, node_input, raise_on_wait=True)
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


run_intake.wait_for_output = True


def hydrate_intake_state(ctx: Context, node_input) -> Event:
    """Merge structured intake output into session state for downstream nodes."""
    form = ProcurementForm.model_validate(node_input)
    return Event(
        state={
            **form.model_dump(),
            "legal_reviewer_output": "",
            "security_reviewer_output": "",
            "rejection_reason": "",
            "rejection_notified": False,
            "purchase_approved": False,
        },
        output=node_input,
    )


def notify_rejection(ctx: Context, node_input) -> Event:
    """Single user-facing denial message; workflow ends until the user replies."""
    reason = ctx.state.get("rejection_reason") or "Request denied."
    return Event(
        message=(
            f"Your procurement request was not approved: {reason}\n\n"
            "Reply here if you'd like to submit a new request."
        ),
        state={"rejection_notified": True},
    )


def routing_logic(ctx: Context, node_input) -> Event:
    """Route by legal/security outcome, cost threshold, and approval state."""
    session_id = ctx.session.id

    #! To do in workshop: Save state to database

    legal = str(ctx.state.get("legal_reviewer_output", ""))
    security = str(ctx.state.get("security_reviewer_output", ""))
    cost = float(ctx.state.get("cost", 0) or 0)

    #! To do in workshop: Check for legal agent rejection

    #! To do in workshop: Check for security agent failure

    #! To do in workshop: Check for cost threshold and purchase approval state

    #! To do in workshop: If all checks pass, route to complete


def route_after_manager(ctx: Context, node_input) -> Event:
    """After manager step: complete on approval, loop to intake on rejection."""
    if ctx.state.get("purchase_approved"):
        return Event(route="complete")
    return Event(route="reject")


def complete_procurement(ctx: Context, node_input) -> Event:
    """Terminal node: user-visible completion message."""
    software = ctx.state.get("software_name", "the requested software")
    return Event(message=f"Procurement request for {software} is complete. Thank you!")
