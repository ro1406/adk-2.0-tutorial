"""LLM agent definitions for the graph-based procurement workflow."""

from google.adk import Agent

from .schemas import ProcurementForm

# Task-mode agent: multi-turn intake until ProcurementForm is complete.
# Not placed on static graph edges — dispatched via run_intake in routing.py.
intake_specialist = Agent(
    name="intake_specialist",
    model="gemini-3.1-flash-lite",
    mode="task",
    wait_for_output=True,
    output_schema=ProcurementForm,
    instruction=(
        "You are a procurement intake specialist. Gather the software name, "
        " yearlycost (AED), and business justification from the user. Ask clarifying "
        "questions until you have all three fields, then call finish_task with "
        "the structured result. If the user provides a monthly cost, convert it to a yearly cost in AED (multiply by 12 and 1USD = 3.67 AED).\n\n"
        "You are the only agent that talks to the end user.\n\n"
        "If {rejection_notified?} is true, the user was already told why the "
        "request was denied. Do not repeat the denial or claim the request was "
        "submitted or approved. Wait for their reply and collect a fresh request "
        "(software name, yearly cost in AED, justification), then finish_task.\n\n"
        "Otherwise gather the three fields, then finish_task."
    ),
    description="Collects structured procurement requests via multi-turn chat.",
)

# Graph nodes default to single_turn when mode is omitted.
_INTERNAL_REVIEW_PREFIX = (
    "Internal workflow review only — do not greet or address the end user. "
    "Output a single-line verdict for routing (not a conversation).\n\n"
)

legal_reviewer = Agent(
    name="legal_reviewer",
    model="gemini-3.1-flash-lite",
    mode="single_turn",
    rerun_on_resume=False,
    instruction=(
        _INTERNAL_REVIEW_PREFIX + "Review this procurement request for legal/compliance risk.\n"
        "Software: {software_name?}\n"
        "Cost: {cost?}\n"
        "Justification: {justification?}\n\n"
        "If it sounds highly dangerous or illegal (e.g. hacking tools, "
        "surveillance malware), output exactly: REJECT: [Reason]. "
        "Otherwise output exactly: Legal: PASS"
    ),
    output_key="legal_reviewer_output",
    description="Legal and compliance review.",
)

security_reviewer = Agent(
    name="security_reviewer",
    model="gemini-3.1-flash-lite",
    mode="single_turn",
    rerun_on_resume=False,
    instruction=(
        _INTERNAL_REVIEW_PREFIX + "Review security posture for this software request.\n"
        "Software: {software_name?}\n"
        "Cost: {cost?}\n\n"
        "If the tool is unsafe for enterprise use, output exactly: "
        "Security: FAIL: [Reason]. Otherwise output exactly: Security: PASS"
    ),
    output_key="security_reviewer_output",
    description="Security review.",
)
