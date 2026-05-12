import re
from typing import Tuple

# Simple prompt injection heuristics. Keep patterns tight to avoid false positives.
_PROMPT_INJECTION_PATTERNS = [
    r"\bignore (all|any|previous) (instructions|directions|rules)\b",
    r"\bdisregard (all|any|previous) (instructions|directions|rules)\b",
    r"\byou are now\b",
    r"\bact as (a|an) (system|developer)\b",
    r"\bsystem prompt\b",
    r"\bdeveloper message\b",
    r"\bjailbreak\b",
    r"\bbypass\b",
    r"\breveal (the )?(system|developer) (prompt|message)\b",
]

_PROMPT_INJECTION_RE = re.compile(
    "|".join(_PROMPT_INJECTION_PATTERNS), re.IGNORECASE)


def detect_prompt_injection(message: str) -> bool:
    if not message:
        return False
    return bool(_PROMPT_INJECTION_RE.search(message))


def validate_user_input(message: str) -> Tuple[bool, str]:
    if detect_prompt_injection(message):
        return False, "Input blocked by prompt-injection guardrail."
    return True, ""
