"""Context window awareness and auto-compaction tools.

Provides Miguel with awareness of how much context has been consumed in the
current conversation, and tools to proactively save state and compact when
running low. This prevents context exhaustion on complex, multi-step tasks.

Approach: Since we can't directly query the API for token counts, we estimate
based on character count of the conversation messages (roughly 3.5 chars per
token for English text). The model's context window size is known from config.
"""

from miguel.agent.config import MODEL_CONTEXT_LIMITS
from miguel.agent.tools.error_utils import safe_tool

# Approximate chars per token for estimation (conservative for mixed content)
CHARS_PER_TOKEN = 3.5

# Thresholds
THRESHOLD_WARNING = 0.60   # 60% — start being efficient
THRESHOLD_CRITICAL = 0.80  # 80% — save state and compact


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text using character-based heuristic."""
    return int(len(text) / CHARS_PER_TOKEN)


def _get_context_limit(model_id: str = "") -> int:
    """Get the context window limit for the current model."""
    return MODEL_CONTEXT_LIMITS.get(model_id, MODEL_CONTEXT_LIMITS["default"])


@safe_tool
def check_context(
    conversation_chars: int,
    model_id: str = "claude-opus-4-6",
) -> str:
    """Estimate current context window usage and get recommendations.

    Call this periodically during complex tasks to monitor context consumption.
    Estimate total characters in the conversation so far (messages + tool outputs)
    and pass that count.

    Rough guide for conversation_chars:
    - Short conversation (5-10 exchanges): ~10,000-30,000 chars
    - Medium conversation (15-25 exchanges): ~50,000-100,000 chars
    - Long conversation with tool outputs: ~100,000-300,000 chars
    - Self-improvement batch: ~200,000-500,000 chars

    Args:
        conversation_chars: Estimated total characters in messages and tool outputs so far.
        model_id: The model ID to check limits against. Default: claude-opus-4-6.

    Returns:
        Context usage report with percentage, tokens remaining, and recommendations.
    """
    estimated_tokens = int(conversation_chars / CHARS_PER_TOKEN)
    context_limit = _get_context_limit(model_id)

    # System prompt + tool definitions overhead (~15k tokens typical for Miguel)
    system_overhead = 15_000
    effective_limit = context_limit - system_overhead

    usage_pct = estimated_tokens / effective_limit if effective_limit > 0 else 1.0
    remaining_tokens = max(0, effective_limit - estimated_tokens)

    lines = [
        "## Context Window Status",
        f"- **Estimated tokens used:** ~{estimated_tokens:,} / {effective_limit:,} effective",
        f"- **Usage:** {usage_pct:.1%}",
        f"- **Remaining:** ~{remaining_tokens:,} tokens",
        "",
    ]

    if usage_pct < THRESHOLD_WARNING:
        lines.append("✅ **COMFORTABLE** — Plenty of context remaining. Continue normally.")
    elif usage_pct < THRESHOLD_CRITICAL:
        lines.extend([
            "⚠️ **WARNING** — Context usage moderate. Recommendations:",
            "- Delegate remaining heavy work to sub-agents",
            "- Be concise — avoid reading large files or generating long code inline",
            "- Save intermediate results with `remember()` instead of holding in context",
        ])
    else:
        lines.extend([
            "🔴 **CRITICAL** — Context running low! Immediate actions:",
            "1. Use `auto_compact()` NOW to save state to memory",
            "2. Delegate remaining work to sub-agents (fresh context)",
            "3. Finish primary task, skip secondary updates (README, docs)",
            "4. If significant work remains, save state and ask user to continue in new conversation",
        ])

    return "\n".join(lines)


@safe_tool
def auto_compact(
    task_description: str,
    progress_summary: str,
    remaining_work: str,
    key_decisions: str = "",
) -> str:
    """Save current task state to persistent memory for context recovery.

    Call this when context is running low or before complex delegations.
    Saves a structured snapshot so work can continue seamlessly, even in
    a new conversation.

    Args:
        task_description: What you're working on (e.g. "Implementing cap-019").
        progress_summary: What's been completed so far.
        remaining_work: What still needs to be done.
        key_decisions: Important decisions or context that shouldn't be lost.

    Returns:
        Confirmation that state was saved, with recovery instructions.
    """
    if not task_description.strip():
        return "Error: task_description cannot be empty."
    if not progress_summary.strip():
        return "Error: progress_summary cannot be empty."

    from miguel.agent.tools.memory_tools import _get_conn
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    state_parts = [
        f"TASK: {task_description.strip()}",
        f"PROGRESS: {progress_summary.strip()}",
        f"REMAINING: {remaining_work.strip()}",
    ]
    if key_decisions and key_decisions.strip():
        state_parts.append(f"DECISIONS: {key_decisions.strip()}")
    state = "\n".join(state_parts)

    conn = _get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM memories WHERE key = ? AND category = ?",
            ("compacted_state", "context"),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE memories SET value = ?, updated_at = ? WHERE id = ?",
                (state, now, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO memories (key, value, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                ("compacted_state", state, "context", now, now),
            )
        conn.commit()
    finally:
        conn.close()

    return (
        "✅ **State saved to persistent memory** (key: `compacted_state`)\n\n"
        f"```\n{state}\n```\n\n"
        "**To recover:** `recall('compacted_state', category='context')`"
    )