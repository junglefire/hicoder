## Why

HiCoder 项目旨在用 Python 实现一个 Codex 风格的编码代理。项目选择基于 AgentScope 框架组合构建，而非从零实现。当前仓库仅有研究文档，需要建立项目骨架，基于 AgentScope 的配置/认证体系完成初始化，为后续迭代奠定运行基础。

## What Changes

- 创建 Python 项目骨架，依赖 `agentscope` 作为核心框架
- 基于 AgentScope 的 `Credential` 体系实现 API Key 读取与验证
- 实现三层配置加载（内置默认 → 用户 `~/.hicoder/config.toml` → 项目 `.hicoder/config.toml`），配置中指定 AgentScope 的模型和凭证
- 支持 OpenAI 和 Anthropic 两种提供商
- 缺失 API Key 时给出明确错误提示

## Capabilities

### New Capabilities

- `config-system`: 三层配置加载与合并，TOML 解析，映射到 AgentScope 模型配置
- `auth`: 基于 AgentScope `Credential` 模块的 API Key 解析（环境变量优先、配置文件回退）

### Modified Capabilities

<!-- 无已有能力需要修改 -->

## Impact

- 新增 `hicoder/` 包目录结构
- 新增 `config/default.toml` 内置默认配置
- 新增 `pyproject.toml` 项目定义，依赖 `agentscope`
- 新增 `tests/` 测试目录
- AgentScope 已提供：`pydantic`、`mcp`、`openai`、`anthropic` 等依赖，无需额外声明
