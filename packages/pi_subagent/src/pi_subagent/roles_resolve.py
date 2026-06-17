"""Merge callable_agents with metadata.default_subagent_roles (Go parity)."""

from __future__ import annotations

from typing import Any

from pi_subagent.types import CallableAgentRef, SubAgentSnapshot


def parse_callable_agent_refs(
    callable_agents: list[CallableAgentRef] | None,
) -> list[CallableAgentRef]:
    if not callable_agents:
        return []
    return list(callable_agents)


def parse_default_subagent_roles(
    metadata: dict[str, Any] | None,
) -> dict[str, str]:
    """Return agent_id -> role from parent metadata."""
    if not metadata:
        return {}

    raw = metadata.get("default_subagent_roles")
    if raw is None:
        return {}

    out: dict[str, str] = {}

    if isinstance(raw, list):
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            agent_id = entry.get("id")
            role = entry.get("role")
            if isinstance(agent_id, str) and agent_id and isinstance(role, str) and role:
                out[agent_id] = role
        return out

    if isinstance(raw, dict):
        for role, agent_id in raw.items():
            if isinstance(agent_id, str) and agent_id and isinstance(role, str) and role:
                out[agent_id] = role
        return out

    raise ValueError("parse default_subagent_roles: unsupported shape")


def has_default_subagent_roles(metadata: dict[str, Any] | None) -> bool:
    try:
        return bool(parse_default_subagent_roles(metadata))
    except ValueError:
        return False


def merge_callable_with_role_defaults(
    callable_agents: list[CallableAgentRef] | None,
    metadata: dict[str, Any] | None,
) -> tuple[list[CallableAgentRef], dict[str, str]]:
    roles_by_id = parse_default_subagent_roles(metadata)
    refs = parse_callable_agent_refs(callable_agents)

    if not refs and roles_by_id:
        refs = [
            CallableAgentRef(type="agent", id=agent_id, version=1)
            for agent_id in roles_by_id
        ]

    role_for_ref: dict[str, str] = {}
    for ref in refs:
        if not ref.id:
            continue
        role = roles_by_id.get(ref.id)
        if role:
            role_for_ref[ref.id] = role

    return refs, role_for_ref


def tag_subagent_role(
    agent: SubAgentSnapshot,
    role: str,
) -> SubAgentSnapshot:
    if not role:
        return agent
    metadata = dict(agent.metadata or {})
    metadata["subagent_role"] = role
    return agent.model_copy(update={"metadata": metadata})
