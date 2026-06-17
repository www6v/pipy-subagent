"""Tests for pi_subagent role merge and DB resolution."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from pi_subagent.resolve import enrich_parent_for_delegation, resolve_sub_agents
from pi_subagent.roles_resolve import (
    merge_callable_with_role_defaults,
    parse_default_subagent_roles,
    tag_subagent_role,
)
from pi_subagent.store import SubAgentStore
from pi_subagent.types import CallableAgentRef, SubAgentSnapshot


def _seed_agent(db_path: Path, agent_id: str, name: str) -> None:
    config = {
        "id": agent_id,
        "name": name,
        "model": "faux/test",
        "system_prompt": f"{name} prompt",
        "version": 1,
    }
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO agents (id, tenant_id, config, created_at)
            VALUES (?, 'default', ?, 1)
            """,
            (agent_id, json.dumps(config)),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def agent_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "oma.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE agents (
                id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER,
                archived_at INTEGER,
                PRIMARY KEY (id, tenant_id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_parse_default_subagent_roles_object_form() -> None:
    roles = parse_default_subagent_roles(
        {"default_subagent_roles": {"explore": "agt_x", "plan": "agt_y"}}
    )
    assert roles == {"agt_x": "explore", "agt_y": "plan"}


def test_parse_default_subagent_roles_array_form() -> None:
    roles = parse_default_subagent_roles(
        {
            "default_subagent_roles": [
                {"id": "agt_x", "role": "explore"},
                {"id": "agt_y", "role": "plan"},
            ]
        }
    )
    assert roles == {"agt_x": "explore", "agt_y": "plan"}


def test_merge_callable_with_role_defaults_expands_roles() -> None:
    refs, roles = merge_callable_with_role_defaults(
        None,
        {"default_subagent_roles": {"explore": "agt_worker"}},
    )
    assert len(refs) == 1
    assert refs[0].id == "agt_worker"
    assert roles["agt_worker"] == "explore"


def test_tag_subagent_role_sets_metadata() -> None:
    snap = SubAgentSnapshot(id="agt_worker", name="worker", model="faux/test")
    tagged = tag_subagent_role(snap, "plan")
    assert tagged.metadata is not None
    assert tagged.metadata["subagent_role"] == "plan"


def test_resolve_sub_agents_from_callable_agents(agent_db: Path) -> None:
    _seed_agent(agent_db, "agt_worker", "worker")
    parent = SubAgentSnapshot(
        id="agt_parent",
        name="parent",
        model="faux/test",
        callable_agents=[CallableAgentRef(id="agt_worker")],
    )
    out = resolve_sub_agents(
        parent=parent,
        tenant_id="default",
        database_path=str(agent_db),
        store=SubAgentStore(str(agent_db)),
    )
    assert out["agt_worker"].name == "worker"


def test_resolve_sub_agents_from_default_roles(agent_db: Path) -> None:
    _seed_agent(agent_db, "agt_worker", "worker")
    parent = SubAgentSnapshot(
        id="agt_parent",
        name="parent",
        model="faux/test",
        metadata={"default_subagent_roles": {"explore": "agt_worker"}},
    )
    out = resolve_sub_agents(
        parent=parent,
        tenant_id="default",
        database_path=str(agent_db),
        store=SubAgentStore(str(agent_db)),
    )
    assert out["agt_worker"].metadata is not None
    assert out["agt_worker"].metadata["subagent_role"] == "explore"


def test_enrich_parent_for_delegation_expands_callable() -> None:
    parent = SubAgentSnapshot(
        id="agt_parent",
        name="parent",
        model="faux/test",
        metadata={"default_subagent_roles": {"plan": "agt_worker"}},
    )
    enriched = enrich_parent_for_delegation(parent)
    assert enriched.callable_agents is not None
    assert enriched.callable_agents[0].id == "agt_worker"
