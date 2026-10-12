"""Agent tools: search_docs, read_chunk, escalate.

Every tool result passes through the guardrail screen before the agent sees it.
"""
import json

from . import guardrails
from .retriever import Retriever

_retriever = None


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def search_docs(query: str) -> str:
    """Semantic search over the product docs. Returns screened chunks."""
    chunks = _get_retriever().search(query)
    clean, dropped = guardrails.screen_chunks(chunks)
    payload = {
        "chunks": [
            {"id": c["id"], "source": c["source"], "text": c["text"]}
            for c in clean
        ],
        "dropped_by_policy": dropped,  # agent is told what was excluded + why
    }
    return json.dumps(payload)


def read_chunk(chunk_id: str) -> str:
    """Fetch one full chunk by id. Returns screened text."""
    chunk = _get_retriever().read_chunk(chunk_id)
    if not chunk:
        return json.dumps({"error": f"no chunk with id {chunk_id}"})
    clean, dropped = guardrails.screen_chunks([chunk])
    if dropped:
        return json.dumps({"error": "chunk excluded by policy", "detail": dropped})
    return json.dumps(
        {"id": clean[0]["id"], "source": clean[0]["source"], "text": clean[0]["text"]}
    )


def escalate(reason: str) -> str:
    """Hand off to a human when the docs can't answer."""
    return json.dumps(
        {"status": "escalated", "reason": reason,
         "message": "A support agent will follow up by email."}
    )


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search the Meridian Cloud product docs for relevant passages.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_chunk",
            "description": "Read one full doc chunk by its id for more detail.",
            "parameters": {
                "type": "object",
                "properties": {"chunk_id": {"type": "string"}},
                "required": ["chunk_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate",
            "description": "Escalate to a human support agent when the docs cannot answer.",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    },
]

_IMPLEMENTATIONS = {
    "search_docs": search_docs,
    "read_chunk": read_chunk,
    "escalate": escalate,
}


def dispatch(name: str, arguments: dict) -> str:
    fn = _IMPLEMENTATIONS.get(name)
    if not fn:
        return json.dumps({"error": f"unknown tool: {name}"})
    return fn(**arguments)
