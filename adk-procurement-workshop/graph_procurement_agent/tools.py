"""Purchase execution helpers for the graph workflow (no tool confirmation)."""


def record_purchase_in_state(state, software_name: str, cost: float) -> str:
    """Record an approved purchase in workflow state."""
    state["purchase_approved"] = True
    state["rejection_reason"] = ""
    message = (
        f"Purchase order executed for {software_name} at {cost:,.2f} AED. "
        "Thank you for approving this purchase."
    )
    state["manager_message"] = message
    return message
