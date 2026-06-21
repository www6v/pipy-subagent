# piPy-subagent

A host-agnostic sub-agent delegation library for multi-agent AI systems. Enables parent agents to delegate tasks to specialized sub-agents with isolated execution contexts, role-based prompts, and comprehensive event tracking.

## 项目特性

### 核心功能
- **多智能体委托系统**: 支持父智能体向子智能体委托任务，实现任务分解和并行处理
- **运行时隔离**: 基于 ContextVar 的线程级运行时隔离，确保不同委托任务的上下文独立性
- **角色系统**: 内置探索、规划、验证等角色提示词，与 Claude Code builtInAgents 对齐
- **后台任务执行**: 支持异步后台任务执行，立即返回任务 ID，通过事件通知完成状态
- **深度限制**: 可配置的委托深度限制（默认最大深度 3），防止无限递归

### 智能体管理
- **动态工具注册**: 自动为可调用的子智能体生成 `call_agent_*` 工具
- **通用子智能体**: 提供通用子智能体工具，用于处理临时性、专注性子任务
- **配置存储**: 从 SQLite 数据库（oma.db）加载智能体配置，支持多租户
- **元数据支持**: 支持通过元数据配置子智能体角色和通用子智能体启用状态

### 执行环境
- **沙箱共享**: 子智能体与父智能体共享文件系统沙箱，文件持久化
- **工具集控制**: 通用子智能体提供受限工具集（bash、read、write、edit、grep、glob）
- **MCP 代理**: 支持 MCP 服务器代理配置，实现工具扩展
- **环境变量**: 支持自定义环境变量传递给子智能体

### 事件系统
- **生命周期事件**: 完整的子智能体生命周期事件追踪（创建、启动、完成、空闲）
- **任务追踪**: 通过 task_id 和 thread_id 追踪后台任务执行状态
- **错误处理**: 统一的错误处理和事件上报机制
- **事件发射**: 可配置的事件发射函数，集成到主机系统

### 技术特性
- **异步优先**: 全异步设计，基于 asyncio 实现高效并发
- **类型安全**: 使用 Pydantic 进行数据验证和类型检查
- **依赖管理**: 基于 uv 的现代 Python 依赖管理
- **测试覆盖**: 完整的单元测试和端到端测试

## 项目架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Host Application                          │
│                    (OMA / Other Frameworks)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 配置运行时
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Extension Layer                                │
│                  subagent_extension.py                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  register(api)                                          │   │
│  │  - 获取 SubAgentRuntime                                 │   │
│  │  - 注册 call_agent_* 工具                               │   │
│  │  - 注册 general_subagent 工具                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 工具调用
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Layer                                    │
│                       tools.py                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │  CallAgentTool           │  │  GeneralSubagentTool     │    │
│  │  - call_agent_{id}       │  │  - general_subagent      │    │
│  │  - 动态生成              │  │  - 通用子智能体          │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 委托请求
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Delegate Layer                                │
│                      delegate.py                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  delegate_to_agent()                                   │   │
│  │  - 深度检查                                             │   │
│  │  - 子智能体解析                                         │   │
│  │  - 同步/后台执行选择                                    │   │
│  │  - 事件发射                                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  resolve_sub_agent()                                    │   │
│  │  - 通用子智能体 (_general_subagent)                     │   │
│  │  - 配置子智能体 (runtime.sub_agents)                     │   │
│  │  - 角色应用 (_apply_subagent_role)                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 运行时访问
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Runtime Layer                                  │
│                      runtime.py                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SubAgentRuntime (ContextVar)                           │   │
│  │  - session_id, workdir                                  │   │
│  │  - parent_agent, sub_agents                            │   │
│  │  - run_sub_turn (host callback)                         │   │
│  │  - depth, max_depth                                     │   │
│  │  - background_tasks                                     │   │
│  │  - emit_event, mcp_proxy, environment                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 配置加载
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Store Layer                                   │
│                       store.py                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SubAgentStore                                          │   │
│  │  - SQLite 数据库访问 (oma.db)                           │   │
│  │  - 多租户支持                                           │   │
│  │  - 配置解析和验证                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  subagent_snapshot_from_config()                         │   │
│  │  - 配置到 SubAgentSnapshot 转换                          │   │
│  │  - 元数据解析                                           │   │
│  │  - callable_agents 规范化                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 角色提示
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Roles Layer                                   │
│                       roles.py                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  内置角色                                               │   │
│  │  - explore: 只读探索                                    │   │
│  │  - plan: 规划生成                                       │   │
│  │  - verify: 验证测试                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  agent_snapshot_with_role()                             │   │
│  │  - 应用角色提示词到智能体快照                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ 数据结构
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Types Layer                                   │
│                       types.py                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SubAgentSnapshot                                       │   │
│  │  - id, name, model, aux_model                           │   │
│  │  - system_prompt, description                           │   │
│  │  - tools, mcp_servers                                   │   │
│  │  - callable_agents, metadata                            │   │
│  │  - enable_general_subagent (property)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  CallableAgentRef                                      │   │
│  │  - type, id, version                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SubTurnResult                                          │   │
│  │  - events: list[dict]                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 执行流程

### 同步委托流程
```
父智能体
  ↓
调用 call_agent_{id}(message)
  ↓
CallAgentTool.execute()
  ↓
delegate_to_agent(agent_id, message, run_in_background=False)
  ↓
检查深度限制 → resolve_sub_agent() → 创建 thread_id
  ↓
发射 thread_created 事件
  ↓
run_sub_turn() → 子智能体执行
  ↓
extract_assistant_text() → 提取结果
  ↓
发射 thread_idle 和 sub_agent_completed 事件
  ↓
返回文本结果给父智能体
```

### 后台委托流程
```
父智能体
  ↓
调用 call_agent_{id}(message, run_in_background=True)
  ↓
CallAgentTool.execute()
  ↓
delegate_to_agent(agent_id, message, run_in_background=True)
  ↓
检查深度限制 → resolve_sub_agent() → 创建 thread_id 和 task_id
  ↓
发射 thread_created 和 sub_agent_started 事件
  ↓
创建后台 asyncio.Task
  ↓
立即返回 task_id 和 thread_id
  ↓
后台执行 → 完成后发射 sub_agent_completed 事件
```

## 安装

```bash
# 使用 uv 安装依赖
uv sync

# 或使用 pip
pip install -e .
```

## 使用示例

### 配置运行时

```python
from pi_subagent.runtime import SubAgentRuntime, configure_subagent_runtime
from pi_subagent.types import SubAgentSnapshot

runtime = SubAgentRuntime(
    session_id="session_123",
    workdir="/path/to/workdir",
    parent_agent=SubAgentSnapshot(
        id="parent",
        name="Parent Agent",
        model="claude-3-5-sonnet",
        system_prompt="You are a helpful assistant",
    ),
    run_sub_turn=your_host_callback_function,
    sub_agents={
        "explorer": SubAgentSnapshot(
            id="explorer",
            name="Explorer",
            model="claude-3-5-sonnet",
            system_prompt="You explore codebases",
        ),
    },
)

token = configure_subagent_runtime(runtime)
```

### 注册扩展

```python
from pi_subagent.extensions.subagent_extension import register

register(api)  # api 是主机的工具注册 API
```

### 委托任务

```python
# 同步委托
result = await delegate_to_agent(
    agent_id="explorer",
    message="Search for all Python files in the project"
)

# 后台委托
result = await delegate_to_agent(
    agent_id="explorer",
    message="Analyze the codebase structure",
    run_in_background=True
)
# 返回: "Background sub-agent started. task_id=xxx thread_id=xxx agent_id=explorer"
```

### 使用角色

```python
# 在智能体配置中通过 metadata 指定角色
agent_config = {
    "id": "code_reviewer",
    "name": "Code Reviewer",
    "model": "claude-3-5-sonnet",
    "metadata": {
        "subagent_role": "verify"  # 使用 verify 角色
    }
}
```

## 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest packages/pi_subagent/tests/test_call_agent.py
uv run pytest packages/pi_subagent/tests/test_subagent_e2e.py
```

## 依赖

- `pi-agent`: 智能体框架核心
- `pi-ai`: AI 模型集成
- `pydantic>=2.0`: 数据验证
- `pytest>=8.0`: 测试框架
- `pytest-asyncio>=0.24`: 异步测试支持

## 项目结构

```
piPy-subagent/
├── extensions/
│   └── subagent_extension.py    # 主机扩展注册层
├── packages/
│   └── pi_subagent/
│       ├── src/
│       │   └── pi_subagent/
│       │       ├── __init__.py
│       │       ├── delegate.py      # 委托逻辑
│       │       ├── events.py        # 事件处理
│       │       ├── paths.py         # 路径工具
│       │       ├── resolve.py       # 子智能体解析
│       │       ├── roles.py         # 角色定义
│       │       ├── roles_resolve.py # 角色解析
│       │       ├── runtime.py       # 运行时管理
│       │       ├── store.py         # 数据库存储
│       │       ├── tools.py         # 工具定义
│       │       └── types.py         # 数据类型
│       ├── tests/                  # 测试套件
│       └── pyproject.toml
├── pyproject.toml                  # 工作空间配置
└── readme.md
```

## 许可证

本项目采用与 piPy 项目相同的许可证。
