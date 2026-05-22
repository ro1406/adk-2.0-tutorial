"""Collaborative agent team: coordinator delegates to task/single_turn sub-agents."""

from google.adk import Agent

from .schemas import ProcurementForm
from .tools import purchase_tool

intake_specialist = Agent(
    name="intake_specialist",
    model="gemini-3.1-flash-lite",
    mode="task",
    output_schema=ProcurementForm,
    instruction=(
        "You are a procurement intake specialist. Gather software name, yearly cost "
        "in AED, and business justification. Ask clarifying questions until "
        "complete, then call finish_task with the structured result. If the user provides a monthly cost, convert it to a yearly cost in AED (multiply by 12 and 1USD = 3.67 AED).\n\n"
        "You are the only agent that talks to the end user. If the coordinator "
        "already explained a rejection, do not repeat it or claim the request "
        "was submitted. Collect a fresh request when the user is ready."
    ),
    description=(
        "Collects structured procurement requests. Use when starting or " "restarting intake after a rejection."
    ),
)

_INTERNAL_REVIEW_PREFIX = (
    "Internal workflow review only — do not greet or address the end user. "
    "Output a single-line verdict for routing (not a conversation).\n\n"
)

legal_reviewer = Agent(
    name="legal_reviewer",
    model="gemini-3.1-flash-lite",
    mode="single_turn",
    instruction=(
        _INTERNAL_REVIEW_PREFIX + "Review this procurement for legal/compliance risk.\n"
        "Software: {software_name?}\n"
        "Cost: {cost?}\n"
        "Justification: {justification?}\n\n"
        "If highly dangerous or illegal, output exactly: REJECT: [Reason]. "
        "Otherwise output exactly: Legal: PASS"
    ),
    description="Legal and compliance review. Returns REJECT or Legal: PASS.",
)

security_reviewer = Agent(
    name="security_reviewer",
    model="gemini-3.1-flash-lite",
    mode="single_turn",
    instruction=(
        _INTERNAL_REVIEW_PREFIX + "You have NO tools. Do not ask for tools, scans, or external systems. "
        "Judge only from the request fields below (typical SaaS/business software is fine).\n\n"
        "Software: {software_name?}\n"
        "Cost (AED): {cost?}\n"
        "Justification: {justification?}\n\n"
        "Use this rubric:\n"
        "- PASS: mainstream business software (e.g. Google Drive, Slack, Zoom, Figma, "
        "Microsoft 365, Adobe, Notion, Claude Code, GitHub Copilot).\n"
        "- FAIL only for clearly high-risk requests (e.g. exploit frameworks, "
        "credential stealers, RATs, illegal hacking tools, unvetted data exfiltration).\n\n"
        "Output exactly one line: either 'Security: PASS' or "
        "'Security: FAIL: [short reason]'."
    ),
    description=(
        "Security review from request metadata only (no tools). " "Returns Security: PASS or Security: FAIL: reason."
    ),
)

manager_override = Agent(
    name="manager_override",
    model="gemini-3.1-flash-lite",
    mode="single_turn",
    instruction=(
        "Approve high-cost purchase for {software_name?} at {cost?} AED. "
        "Call execute_purchase_order with software_name and cost. "
        "Human confirmation is required in the UI."
    ),
    tools=[purchase_tool],
    description=("Manager executes purchase orders over 500 AED with human confirmation."),
)

procurement_coordinator = Agent(
    name="procurement_coordinator",
    model="gemini-3.1-flash-lite",
    instruction="""You are the enterprise procurement coordinator.

Workflow:
1. Delegate intake to intake_specialist via request_task_intake_specialist
   until you receive a complete ProcurementForm (software_name, cost, justification).
2. After intake completes, delegate legal_reviewer and security_reviewer (you may call both).
   They read software_name, cost, and justification from session state — no tools.
3. If legal output contains REJECT or security contains FAIL, send the user ONE
   message with that verdict (do not also quote conflicting reviewer outcomes),
   then delegate intake_specialist only after the user replies with a new request.
4. If cost is greater than 500 AED, delegate manager_override to execute the purchase.
5. Otherwise confirm the request is approved and complete.

Always use the request_task_* tools to delegate. Do not invent data; use sub-agent results.
""",
    sub_agents=[
        intake_specialist,
        legal_reviewer,
        security_reviewer,
        manager_override,
    ],
)
