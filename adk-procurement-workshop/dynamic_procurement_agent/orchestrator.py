"""Dynamic procurement orchestrator — control flow in Python, not graph edges."""

from google.adk import Context
from google.adk.workflow import node

from .routing import (
    complete_event,
    evaluate_decision,
    execute_purchase_node,
    hydrate_intake_state,
    is_approval,
    manager_approval,
    rejection_event,
    run_intake,
    run_reviews_parallel,
)


@node(rerun_on_resume=True, name="procurement_orchestrator")
async def procurement_orchestrator(ctx: Context, node_input):
    """Single dynamic node: intake → reviews → if/else → RequestInput HITL → complete."""
    form = await run_intake(ctx, node_input)
    hydrate_intake_state(ctx, form)

    await run_reviews_parallel(ctx, form)

    decision = evaluate_decision(ctx)

    if decision == "reject":
        yield rejection_event(ctx)
        return

    if decision == "complete":
        yield complete_event(ctx)
        return

    response = await ctx.run_node(
        manager_approval,
        form.model_dump(),
        run_id="manager-approval",
    )
    if not is_approval(response):
        ctx.state["rejection_reason"] = "Manager declined the purchase."
        yield rejection_event(ctx)
        return

    await ctx.run_node(
        execute_purchase_node,
        form.model_dump(),
        run_id="manager-exec",
    )
    yield complete_event(ctx)
