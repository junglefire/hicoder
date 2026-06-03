## Why

迭代 1-2 已实现配置加载、模型接入和流式响应，但缺少核心代理循环。用户提问后模型只能回答一次，无法调用工具、获取结果、继续推理。本迭代实现完整的 Turn 引擎，使代理能闭环工作：构建上下文 → 调模型 → 解析工具调用 → 执行工具 → 返回结果 → 循环直到完成。

## What Changes

- 新增核心代理 Turn 循环引擎（`agent_loop` 异步生成器）
- 新增上下文构建模块，拼装系统提示 + 工具定义 + 对话历史
- 新增 Session 类，管理对话状态和工具注册表
- 新增 `tools` 包：工具注册表 + Shell/Read/Write 三个基础工具
- 扩展 `model_client.py` 支持 tool 参数传递
- `app.py` 的 chat 命令接入 agent_loop，从直接调模型改为走完整循环

## Capabilities

### New Capabilities
- `agent-loop`: 核心 Turn 循环引擎，模型调用 → 工具执行 → 循环直到无工具调用
- `context-builder`: 将系统提示、AGENTS.md 指令、工具定义、对话历史拼装为模型输入
- `session`: 会话生命周期管理，维护对话状态、工具注册表、配置
- `tool-execution`: 工具注册、发现、定义生成、并行执行
- `tool-shell`: Shell 命令执行工具，支持超时控制和输出截断
- `tool-file`: 文件读写工具（read_file / write_file / edit_file）

### Modified Capabilities
- `model-client`: 扩展 `stream()` 方法支持 `tools` 参数，将工具定义传递给模型 API

## Impact

- `hicoder/models/model_client.py`: 新增 `tools` 参数支持
- `hicoder/app.py`: chat 命令从直接调 `_chat_loop` 改为通过 agent_loop 驱动
- 新增 `hicoder/agent_loop.py`、`hicoder/session.py`、`hicoder/tools/` 模块
- `hicoder/config.py`: 新增 `cwd` 字段（工具执行的工作目录）
