"""
claude_agent.py — Agentic loop that drives Claude with tool use.

Each Webex room gets its own conversation history (in-memory).
When Claude calls a tool the loop executes it and feeds the result back
until Claude issues end_turn.
"""

import os
from collections import defaultdict

import anthropic

from .system_prompt import load_system_prompt
from .tools import TOOL_SCHEMAS, execute_tool

# ── Client ────────────────────────────────────────────────────────────────────

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


# ── Conversation history per Webex room ──────────────────────────────────────
# Dict: room_id → list of message dicts (user / assistant turns)

_histories: dict[str, list[dict]] = defaultdict(list)

MAX_HISTORY_TURNS = 20  # keep last N user+assistant pairs to avoid context bloat


def clear_history(room_id: str) -> None:
    """Reset conversation history for a room (e.g. on /reset command)."""
    _histories[room_id].clear()


def _trim_history(room_id: str) -> None:
    """Keep only the last MAX_HISTORY_TURNS pairs so context stays manageable."""
    history = _histories[room_id]
    # Each pair = 1 user + 1 assistant message = 2 items
    max_items = MAX_HISTORY_TURNS * 2
    if len(history) > max_items:
        _histories[room_id] = history[-max_items:]


# ── Main entry point ──────────────────────────────────────────────────────────

def ask(room_id: str, user_message: str) -> str:
    """
    Process a user message in the context of a Webex room.

    Args:
        room_id:      Webex room ID (used as conversation key).
        user_message: Text sent by the engineer (may include file context).

    Returns:
        Claude's final text response.
    """
    client = _get_client()
    system = load_system_prompt()

    # Build messages: history + new user turn
    _histories[room_id].append({"role": "user", "content": user_message})
    _trim_history(room_id)

    messages = list(_histories[room_id])

    # ── Agentic loop ──────────────────────────────────────────────────────────
    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8096,
            thinking={"type": "adaptive"},
            system=system,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # If Claude is done, extract the final text and return
        if response.stop_reason == "end_turn":
            final_text = _extract_text(response)
            # Persist Claude's response to history (store full content for accuracy)
            _histories[room_id].append(
                {"role": "assistant", "content": response.content}
            )
            _trim_history(room_id)
            return final_text

        # Claude wants to use tools
        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            # Append Claude's response (including tool_use blocks) to the conversation
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for tool_block in tool_use_blocks:
                print(f"  [tool] {tool_block.name}({tool_block.input})")
                result = execute_tool(tool_block.name, tool_block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result,
                    }
                )

            # Feed tool results back as the next user turn
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — return whatever text we have
        final_text = _extract_text(response) or f"[stopped: {response.stop_reason}]"
        _histories[room_id].append(
            {"role": "assistant", "content": response.content}
        )
        return final_text


def _extract_text(response: anthropic.types.Message) -> str:
    """Concatenate all text blocks from a response."""
    return "\n".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
