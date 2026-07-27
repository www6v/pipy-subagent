"""Sub-agent session event helpers."""

from __future__ import annotations

import random
import time
from typing import Any

# Wire events that interrupt a streamed assistant text run. OMA emit maps
# streaming replies to many consecutive ``agent.message`` deltas; tool / user
# events mark segment boundaries between assistant rounds.
_SEGMENT_BREAK_TYPES = frozenset(
    {
        "agent.tool_use",
        "agent.tool_result",
        "agent.custom_tool_use",
        "user.message",
    }
)


def new_thread_id() -> str:
    suffix = f"{int(time.time() * 1000):x}{random.randint(0, 0xFFFFFF):06x}"
    return f"sthr_{suffix}"


def new_task_id() -> str:
    suffix = f"{int(time.time() * 1000):x}{random.randint(0, 0xFFFFFF):06x}"
    return f"sbtask_{suffix}"


def _text_from_agent_message(event: dict[str, Any]) -> str:
    parts: list[str] = []
    for block in event.get("content") or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and block.get("text"):
            parts.append(str(block["text"]))
    # Blocks inside one event are usually one text block; join without
    # inventing newlines between streaming deltas.
    return "".join(parts)


def extract_assistant_text(events: list[dict[str, Any]]) -> str:
    """Reconstruct the last assistant reply from session wire events.

    OMA ``emit_oma_events`` streams assistant output as many contiguous
    ``agent.message`` events, each carrying only a text delta. Taking the
    last event alone returns a trailing chunk (e.g. ``\"25\"``); joining
    consecutive deltas recovers the full reply. Non-message events (tool
    rounds, user messages) split segments so multi-round turns still return
    the final assistant answer.
    """
    segments: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            segments.append("".join(current))
            current.clear()

    for event in events:
        if not isinstance(event, dict):
            continue
        etype = event.get("type")
        if etype == "agent.message":
            piece = _text_from_agent_message(event)
            if piece:
                current.append(piece)
            continue
        if etype in _SEGMENT_BREAK_TYPES:
            flush()

    flush()

    for text in reversed(segments):
        stripped = text.strip()
        if stripped:
            return stripped
    return ""
