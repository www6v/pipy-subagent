-- ============================================================================
-- subagent.sql
-- piPy-subagent - 子 Agent 解析扩展 - 数据库使用说明
-- 来源: piPy-subagent/packages/pi_subagent/src/pi_subagent/store.py
-- 数据库: SQLite, 与 oma-platform 共享 oma.db (只读)
--        (OMA_DATABASE_PATH / DATABASE_PATH, 缺省 ./data/oma.db)
-- 说明: 本模块不创建任何表, 也不写入任何数据。它只从平台的 oma.db 中
--        读取 `agents` 表的 config 列 (JSON), 用于解析 callable_agents
--        以及构造 SubAgentSnapshot。
--        `agents` 表的 DDL 由 oma-platform 维护:
--          - SQLite: oma-platform/scripts/sql/platform.sql
--          - MySQL:  oma-platform/scripts/sql/platform_mysql.sql
--          - migration: oma-platform/internal/store/migrations/001_core.sql
-- 为了自包含, 下面给出 `agents` 表当前 DDL 的副本 (仅供参考; 真正的
-- schema-of-record 仍以 oma-platform 的 migration 为准)。
-- ============================================================================

CREATE TABLE IF NOT EXISTS agents (
  id          TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL DEFAULT 'default',
  config      TEXT NOT NULL,
  version     INTEGER NOT NULL,
  created_at  INTEGER NOT NULL,
  updated_at  INTEGER,
  archived_at INTEGER
);

CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id);
