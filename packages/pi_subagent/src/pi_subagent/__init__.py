"""Sub-agent delegation library (host-agnostic)."""

from pi_subagent.delegate import delegate_to_agent, resolve_sub_agent
from pi_subagent.resolve import resolve_sub_agents
from pi_subagent.roles_resolve import (
    merge_callable_with_role_defaults,
    tag_subagent_role,
)
from pi_subagent.runtime import (
    SubAgentRuntime,
    clear_subagent_runtime,
    configure_subagent_runtime,
    get_subagent_runtime,
    reset_subagent_runtime,
)
from pi_subagent.types import SubAgentSnapshot, SubTurnResult

__all__ = [
    "SubAgentRuntime",
    "SubAgentSnapshot",
    "SubTurnResult",
    "clear_subagent_runtime",
    "configure_subagent_runtime",
    "delegate_to_agent",
    "get_subagent_runtime",
    "merge_callable_with_role_defaults",
    "reset_subagent_runtime",
    "resolve_sub_agent",
    "resolve_sub_agents",
    "tag_subagent_role",
]
