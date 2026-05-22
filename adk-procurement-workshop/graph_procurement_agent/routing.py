"""Routing nodes and task-intake bridge for the graph workflow."""

from typing import Any

from google.adk import Context, Event
from google.adk.events import RequestInput
from google.adk.workflow import node

from .agents import intake_specialist
from .db import MockSQLiteSessionService
from .schemas import ProcurementForm
from .tools import record_purchase_in_state

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
            "procurement_complete_notified": False,
            "manager_routed": False,
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
    db.save_state(session_id, ctx.state.to_dict())

    if ctx.state.get("procurement_complete_notified") or ctx.state.get(
        "purchase_approved"
    ):
        return Event(route="complete")

    legal = str(ctx.state.get("legal_reviewer_output", ""))
    security = str(ctx.state.get("security_reviewer_output", ""))
    cost = float(ctx.state.get("cost", 0) or 0)

    if "REJECT" in legal.upper():
        return Event(state={"rejection_reason": legal}, route="reject")

    if "FAIL" in security.upper():
        return Event(
            state={"rejection_reason": security or "Security review failed."},
            route="reject",
        )

    if cost > 500 and not ctx.state.get("purchase_approved"):
        if ctx.state.get("manager_routed"):
            return Event()
        return Event(state={"manager_routed": True}, route="manager")

    return Event(route="complete")


def is_approval(response: Any) -> bool:
    """Parse manager RequestInput response (same as dynamic app)."""
    if response is None:
        return False
    text = str(response).strip().lower()
    if text in ("yes", "y", "approve", "approved"):
        return True
    return text.startswith("yes")


@node(rerun_on_resume=False, name="manager_hitl")
async def manager_hitl(ctx: Context, node_input):
    """Pause for manager Yes/No via RequestInput (ADK dynamic-style HITL)."""
    del node_input
    cost = float(ctx.state.get("cost", 0) or 0)
    software = ctx.state.get("software_name", "the requested software")
    yield RequestInput(
        message=(
            f"Manager approval required: purchase {software} for {cost:,.2f} AED.\n"
            "Reply Yes to approve or No to decline."
        )
    )


manager_hitl.wait_for_output = True


def route_manager_hitl(ctx: Context, node_input) -> Event:
    """Branch on manager Yes/No before purchase execution."""
    if is_approval(node_input):
        return Event(route="approve")
    return Event(
        state={"rejection_reason": "Manager declined the purchase."},
        route="reject",
    )


@node(name="execute_purchase")
def execute_purchase(ctx: Context, node_input) -> str:
    """Execute purchase after RequestInput approval (writes directly to ctx.state)."""
    del node_input
    software = ctx.state.get("software_name", "the requested software")
    cost = float(ctx.state.get("cost", 0) or 0)
    return record_purchase_in_state(ctx.state, software, cost)


def complete_procurement(ctx: Context, node_input) -> Event:
    """Terminal node: user-visible completion message (once per request)."""
    if ctx.state.get("procurement_complete_notified"):
        return Event()

    software = ctx.state.get("software_name", "the requested software")
    message = ctx.state.get("manager_message") or (
        f"Procurement request for {software} is complete. Thank you!"
    )
    return Event(message=message, state={"procurement_complete_notified": True})
