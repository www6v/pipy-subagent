"""Load agent configs from oma.db for sub-agent resolution."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from pi_subagent.types import CallableAgentRef, SubAgentSnapshot


def resolve_database_path(explicit: str | None = None) -> str:
    if explicit:
        path = explicit
    else:
        path = None
        for key in ("OMA_DATABASE_PATH", "DATABASE_PATH"):
            value = os.environ.get(key)
            if value:
                path = value
                break
        if path is None:
            path = "./data/oma.db"
    return os.path.abspath(path)


def _tenant_or_default(tenant_id: str | None) -> str:
    if tenant_id and tenant_id.strip():
        return tenant_id.strip()
    return "default"


class SubAgentStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_agent_config(
        self,
        tenant_id: str | None,
        agent_id: str,
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT config
                FROM agents
                WHERE id = ? AND tenant_id = ?
                """,
                (agent_id, _tenant_or_default(tenant_id)),
            ).fetchone()
        if row is None:
            return None
        try:
            config = json.loads(row["config"])
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(f"parse agent config for {agent_id!r}") from exc
        if not isinstance(config, dict):
            raise ValueError(f"agent config for {agent_id!r} is not an object")
        return config


def _normalize_callable_agents(raw: Any) -> list[CallableAgentRef] | None:
    if raw is None:
        return None
    if not isinstance(raw, list):
        return None
    refs: list[CallableAgentRef] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        agent_id = item.get("id")
        if not isinstance(agent_id, str) or not agent_id:
            continue
        version = item.get("version", 1)
        refs.append(
            CallableAgentRef(
                type=str(item.get("type") or "agent"),
                id=agent_id,
                version=int(version) if isinstance(version, int) else 1,
            )
        )
    return refs or None


def subagent_snapshot_from_config(config: dict[str, Any]) -> SubAgentSnapshot:
    system_prompt = config.get("system_prompt")
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        system_prompt = config.get("system")

    metadata = config.get("metadata")
    meta_dict: dict[str, Any] | None = None
    if isinstance(metadata, dict):
        meta_dict = metadata
    elif isinstance(metadata, str):
        try:
            parsed = json.loads(metadata)
            if isinstance(parsed, dict):
                meta_dict = parsed
        except json.JSONDecodeError:
            meta_dict = None

    tools = config.get("tools")
    mcp_servers = config.get("mcp_servers")
    return SubAgentSnapshot(
        id=str(config.get("id") or ""),
        name=str(config.get("name") or ""),
        model=str(config.get("model") or ""),
        aux_model=config.get("aux_model"),
        system=config.get("system"),
        system_prompt=system_prompt if isinstance(system_prompt, str) else None,
        description=config.get("description"),
        tools=tools if isinstance(tools, list) else None,
        mcp_servers=mcp_servers if isinstance(mcp_servers, list) else None,
        callable_agents=_normalize_callable_agents(config.get("callable_agents")),
        metadata=meta_dict,
        version=int(config.get("version") or 1),
    )
