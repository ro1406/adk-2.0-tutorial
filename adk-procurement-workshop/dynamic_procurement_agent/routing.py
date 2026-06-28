"""Helpers and child nodes for the dynamic procurement orchestrator."""

import asyncio
from typing import Any, Literal

from google.adk import Context, Event
from google.adk.events import RequestInput
from google.adk.workflow import node

from .agents import intake_specialist, legal_reviewer, security_reviewer
from .db import MockSQLiteSessionService
from .schemas import ProcurementForm
from .tools import record_purchase_in_state

db = MockSQLiteSessionService()

_RUN_LEGAL = "legal_review"
_RUN_SECURITY = "security_review"


def _intake_run_id(ctx: Context) -> str:
    generation = int(ctx.state.get("intake_generation") or 0)
    return "intake" if generation == 0 else f"intake-{generation}"


async def run_intake(ctx: Context, node_input) -> ProcurementForm:
    """Task-mode intake via ctx.run_node (cannot sit on static Workflow edges in 2.0)."""
    result = await ctx.run_node(
        intake_specialist,
        node_input,
        run_id=_intake_run_id(ctx),
        raise_on_wait=True,
    )
    if hasattr(result, "model_dump"):
        return ProcurementForm.model_validate(result.model_dump())
    return ProcurementForm.model_validate(result)


def validate_and_save_intake_state(ctx: Context, form: ProcurementForm) -> None:
    """Merge intake output into state and reset downstream review flags."""
    for key, value in form.model_dump().items():
        ctx.state[key] = value
    ctx.state["legal_reviewer_output"] = ""
    ctx.state["security_reviewer_output"] = ""
    ctx.state["rejection_reason"] = ""
    ctx.state["rejection_notified"] = False
    ctx.state["purchase_approved"] = False


async def run_reviews_parallel(ctx: Context, form: ProcurementForm) -> None:
    """Parallel legal + security via ctx.run_node."""
    payload = form.model_dump()
    await asyncio.gather(
        ctx.run_node(legal_reviewer, payload, run_id=_RUN_LEGAL),
        ctx.run_node(security_reviewer, payload, run_id=_RUN_SECURITY),
    )
    db.save_state(ctx.session.id, ctx.state.to_dict())


def evaluate_decision(ctx: Context) -> Literal["reject", "manager", "complete"]:
    """Pure Python routing — no Event(route=...)."""
    legal = str(ctx.state.get("legal_reviewer_output", ""))
    security = str(ctx.state.get("security_reviewer_output", ""))
    cost = float(ctx.state.get("cost", 0) or 0)

    if "REJECT" in legal.upper():
        ctx.state["rejection_reason"] = legal
        return "reject"

    if "FAIL" in security.upper():
        ctx.state["rejection_reason"] = security or "Security review failed."
        return "reject"

    if cost > 500 and not ctx.state.get("purchase_approved"):
        return "manager"

    return "complete"


def is_approval(response: Any) -> bool:
    """Parse manager RequestInput response."""
    if response is None:
        return False
    text = str(response).strip().lower()
    if text in ("yes", "y", "approve", "approved"):
        return True
    return text.startswith("yes")


def rejection_event(ctx: Context) -> Event:
    """Single user-facing denial; workflow ends until the user replies."""
    reason = ctx.state.get("rejection_reason") or "Request denied."
    generation = int(ctx.state.get("intake_generation") or 0)
    return Event(
        message=(
            f"Your procurement request was not approved: {reason}\n\n"
            "Reply here if you'd like to submit a new request."
        ),
        state={
            "rejection_notified": True,
            "intake_generation": generation + 1,
        },
    )


def complete_event(ctx: Context) -> Event:
    """Terminal user-visible message."""
    software = ctx.state.get("software_name", "the requested software")
    message = ctx.state.get("manager_message") or (
        f"Procurement request for {software} is complete. Thank you!"
    )
    return Event(message=message, output={"status": "complete"})


@node(rerun_on_resume=False, name="manager_approval")
async def manager_approval(ctx: Context, node_input):
    """Pause for manager Yes/No via RequestInput (ADK dynamic HITL)."""
    del node_input
    cost = float(ctx.state.get("cost", 0) or 0)
    software = ctx.state.get("software_name", "the requested software")
    yield RequestInput(
        message=(
            f"Manager approval required: purchase {software} for {cost:,.2f} AED.\n"
            "Reply Yes to approve or No to decline."
        )
    )


@node(name="execute_purchase")
def execute_purchase_node(ctx: Context, node_input) -> str:
    """Execute purchase after RequestInput approval (no tool confirmation)."""
    form = ProcurementForm.model_validate(node_input)
    return record_purchase_in_state(ctx.state, form.software_name, form.cost)
