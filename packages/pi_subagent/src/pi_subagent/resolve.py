"""Resolve sub-agent snapshots for a parent agent turn."""

from __future__ import annotations

from pi_subagent.roles_resolve import (
    merge_callable_with_role_defaults,
    tag_subagent_role,
)
from pi_subagent.store import (
    SubAgentStore,
    resolve_database_path,
    subagent_snapshot_from_config,
)
from pi_subagent.types import CallableAgentRef, SubAgentSnapshot


def effective_callable_agent_refs(
    parent: SubAgentSnapshot,
) -> list[CallableAgentRef]:
    refs, _ = merge_callable_with_role_defaults(
        parent.callable_agents,
        parent.metadata,
    )
    return refs


def resolve_sub_agents(
    *,
    parent: SubAgentSnapshot,
    tenant_id: str | None,
    database_path: str | None = None,
    store: SubAgentStore | None = None,
) -> dict[str, SubAgentSnapshot]:
    refs, roles_by_id = merge_callable_with_role_defaults(
        parent.callable_agents,
        parent.metadata,
    )
    if not refs:
        return {}

    agent_store = store or SubAgentStore(resolve_database_path(database_path))
    out: dict[str, SubAgentSnapshot] = {}
    for ref in refs:
        if not ref.id:
            continue
        config = agent_store.get_agent_config(tenant_id, ref.id)
        if config is None:
            raise ValueError(f'callable agent "{ref.id}" not found')
        snap = subagent_snapshot_from_config(config)
        out[ref.id] = tag_subagent_role(snap, roles_by_id.get(ref.id, ""))
    return out


def enrich_parent_for_delegation(
    parent: SubAgentSnapshot,
) -> SubAgentSnapshot:
    refs = effective_callable_agent_refs(parent)
    if not refs:
        return parent
    if parent.callable_agents:
        return parent
    return parent.model_copy(update={"callable_agents": refs})
