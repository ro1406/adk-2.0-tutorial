"""HITL tools and callbacks for the procurement workflow."""

from typing import Any

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.tool_context import ToolContext


def execute_purchase_order(
    software_name: str,
    cost: float,
    tool_context: ToolContext,
) -> str:
    """Execute a purchase order after human confirmation in the ADK Web UI."""
    tool_context.state["purchase_approved"] = True
    tool_context.state["rejection_reason"] = ""
    message = (
        f"Purchase order executed for {software_name} at {cost:,.2f} AED. "
        "Thank you for approving this purchase."
    )
    tool_context.state["manager_message"] = message
    return message


purchase_tool = FunctionTool(execute_purchase_order, require_confirmation=True)


_MANAGER_REJECTION_ERROR = "This tool call is rejected."


def after_manager_tool_callback(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    """Record manager rejection only when the user declines in the UI."""
    del tool, args
    if isinstance(tool_response, dict) and tool_response.get("error") == _MANAGER_REJECTION_ERROR:
        tool_context.state["rejection_reason"] = (
            "Manager rejected the purchase order in the approval UI."
        )
        tool_context.state["purchase_approved"] = False
    return None
