import re
from typing import Tuple

_EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(
    r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"
)
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def _mask(match: re.Match, token: str) -> str:
    return token


def _mask_credit_card(match: re.Match) -> str:
    raw = match.group(0)
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 13 or len(digits) > 19:
        return raw
    return "[REDACTED_CREDIT_CARD]"


def redact_pii(text: str) -> Tuple[str, int]:
    if not text:
        return text, 0

    redacted = text
    redacted, email_count = _EMAIL_RE.subn(
        lambda m: _mask(m, "[REDACTED_EMAIL]"), redacted)
    redacted, phone_count = _PHONE_RE.subn(
        lambda m: _mask(m, "[REDACTED_PHONE]"), redacted)
    redacted, ssn_count = _SSN_RE.subn(
        lambda m: _mask(m, "[REDACTED_SSN]"), redacted)
    redacted, cc_count = _CC_CANDIDATE_RE.subn(_mask_credit_card, redacted)

    return redacted, email_count + phone_count + ssn_count + cc_count
