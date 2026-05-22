"""HITL tools for the collaborative procurement coordinator."""

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext


def execute_purchase_order(
    software_name: str,
    cost: float,
    tool_context: ToolContext,
) -> str:
    """Execute a purchase order after human confirmation in the ADK Web UI."""
    tool_context.state["purchase_approved"] = True
    return (
        f"Purchase order executed for {software_name} at {cost:,.2f} AED. "
        "Thank you for approving this purchase."
    )


purchase_tool = FunctionTool(execute_purchase_order, require_confirmation=True)
