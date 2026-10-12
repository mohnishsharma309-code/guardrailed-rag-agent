"""Deterministic policy layer: PII redaction, prompt-injection detection,
topic blocklists. Pure heuristics — no LLM calls, fully unit-testable."""
import re

# ---------------------------------------------------------------- PII ------
PII_PATTERNS = [
    ("email", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
    ("phone", re.compile(r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:\d[ -]*){13,16}\b")),
]


def redact_pii(text: str):
    """Replace PII with typed markers. Returns (redacted_text, findings)."""
    findings = []
    for name, pattern in PII_PATTERNS:
        text, n = pattern.subn(f"[REDACTED_{name.upper()}]", text)
        if n:
            findings.append({"type": name, "count": n})
    return text, findings


# ------------------------------------------------- prompt injection ---------
INJECTION_PATTERNS = [
    ("ignore-instructions", r"ignor(e|ing)\s+(all\s+)?(previous|prior|above)\s+instructions"),
    ("disregard", r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)"),
    ("system-override", r"\bsystem\s*prompt\b"),
    ("secret-extraction", r"(reveal|disclose|show|tell me).{0,50}(password|secret|api key|token|credentials)"),
    ("role-hijack", r"\b(you are now|pretend (you are|to be))\b"),
    ("jailbreak", r"\b(DAN|jailbreak|do anything now)\b"),
    ("instruction-smuggle", r"note to ai|instruction to (the |an )?ai|developer note:"),
]


def detect_injection(text: str):
    """Return names of matched injection patterns (case-insensitive)."""
    lowered = text.lower()
    return [name for name, pat in INJECTION_PATTERNS if re.search(pat, lowered)]


# ------------------------------------------------------------- screens -----
REFUSAL_PHRASES = [
    "i can't", "i cannot", "i'm not able", "i am not able", "unable to",
    "not able to", "can't help", "won't be able", "don't have",
    "do not have", "not something i can",
]

REFUSAL_TEMPLATE = (
    "I can't help with that. {reason} "
    "I can help with questions about Meridian Cloud's docs instead."
)


def is_refusal(text: str) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in REFUSAL_PHRASES)


def screen_input(query: str, blocked_topics):
    """Stage 1: screen the user's question before it reaches the agent."""
    reasons = []
    injections = detect_injection(query)
    if injections:
        reasons.append(f"prompt-injection pattern: {', '.join(injections)}")
    lowered = query.lower()
    for topic in blocked_topics:
        if topic in lowered:
            reasons.append(f"blocked topic: {topic}")
    _, pii = redact_pii(query)
    if pii:
        reasons.append(f"pii in query (will be redacted): {[f['type'] for f in pii]}")
    blocked = any(not r.startswith("pii in query") for r in reasons)
    return {"blocked": blocked, "reasons": reasons}


def screen_chunks(chunks):
    """Stage 2: screen retrieved chunks. Tainted chunks are dropped.

    Returns (clean_chunks, dropped) where dropped lists chunk ids excluded
    for injection markers, and every kept chunk is PII-redacted.
    """
    clean, dropped = [], []
    for ch in chunks:
        injections = detect_injection(ch["text"])
        if injections:
            dropped.append({"id": ch["id"], "injections": injections})
            continue
        redacted, pii = redact_pii(ch["text"])
        clean.append({**ch, "text": redacted, "pii_redacted": pii})
    return clean, dropped


def screen_output(answer: str):
    """Stage 3: final leak check on the answer before it goes to the user."""
    redacted, pii = redact_pii(answer or "")
    injections = detect_injection(redacted)
    return {
        "answer": redacted,
        "pii_findings": pii,
        "injection_echo": injections,
        "leaked": bool(pii) or bool(injections),
    }
