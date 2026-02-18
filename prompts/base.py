"""
Prompt registry and rendering utilities.
"""
from typing import Any, Dict, Optional, Tuple

from prompts.emi_prompt import EMI_REMINDER_PROMPT
from prompts.sales_prompt import SALES_CALL_PROMPT

DEFAULT_CALL_TYPE = "emi_reminder"

PROMPT_LIBRARY: Dict[str, Dict[str, str]] = {
    "emi_reminder": EMI_REMINDER_PROMPT,
    "sales": SALES_CALL_PROMPT,

    "payment_followup": {
        "system_prompt": """\
ROLE: You are Amit from {bank_name} collections team.
GOAL: Follow up on a previously committed payment and reconfirm a payment date.

CONTEXT:
- Customer: {name}
- Outstanding Amount: INR {amount}
- Prior Commitment Date: {due_date}

RULES:
- Be polite and direct.
- Ask for a concrete payment date if payment is delayed.
- Keep each response under 2 sentences.
- Once you have a date or a clear answer, say goodbye and end the call.
""",
        "initial_greeting": "Hi {name}, this is Amit from {bank_name}. I am calling for a quick payment follow-up.",
    },

    "verification_call": {
        "system_prompt": """\
ROLE: You are Amit from {bank_name}.
GOAL: Verify if you are speaking to the right customer and confirm account follow-up details.

CONTEXT:
- Customer Name on Record: {name}
- Loan Type: {loan_type}
- Due Date: {due_date}

RULES:
- Do not share sensitive account details until identity is confirmed.
- Keep the flow short and professional.
- End the call politely if this is a wrong number.
""",
        "initial_greeting": "Hello, I am Amit from {bank_name}. Am I speaking with {name}?",
    },
}


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def get_prompt_templates(call_type: Optional[str]) -> Tuple[Dict[str, str], str]:
    normalized = (call_type or DEFAULT_CALL_TYPE).strip().lower()
    if normalized in PROMPT_LIBRARY:
        return PROMPT_LIBRARY[normalized], normalized
    return PROMPT_LIBRARY[DEFAULT_CALL_TYPE], DEFAULT_CALL_TYPE


def render_prompt(template: str, context: Dict[str, Any]) -> str:
    sanitized_context = {k: ("" if v is None else v) for k, v in context.items()}
    return template.format_map(_SafeDict(sanitized_context))
