"""Tests for session event helpers."""

from pi_subagent.events import extract_assistant_text


def _msg(text: str) -> dict:
    return {"type": "agent.message", "content": [{"type": "text", "text": text}]}


def test_extract_joins_streaming_deltas():
    """Regression: OMA emit streams deltas as agent.message chunks.

    Taking only the last event used to return a trailing fragment like
    ``\"25\"`` instead of the full reply.
    """
    events = [
        _msg("Here are "),
        _msg("5 LLM papers:\n1. Title A"),
        _msg("\n2. Title B"),
        _msg("\n3. Title C"),
    ]
    assert extract_assistant_text(events) == (
        "Here are 5 LLM papers:\n1. Title A\n2. Title B\n3. Title C"
    )
    # Old behavior (last event only) would have returned this fragment:
    assert events[-1]["content"][0]["text"] == "\n3. Title C"


def test_extract_returns_last_segment_after_tools():
    events = [
        _msg("Searching…"),
        {"type": "agent.tool_use", "name": "web_search", "id": "t1"},
        {
            "type": "agent.tool_result",
            "tool_use_id": "t1",
            "content": [{"type": "text", "text": "hits"}],
        },
        _msg('["Paper One", "Paper Two"]'),
    ]
    assert extract_assistant_text(events) == '["Paper One", "Paper Two"]'


def test_extract_single_complete_message():
    events = [_msg("done")]
    assert extract_assistant_text(events) == "done"


def test_extract_empty():
    assert extract_assistant_text([]) == ""
    assert extract_assistant_text([{"type": "agent.tool_use"}]) == ""
