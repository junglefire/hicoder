## Context

HiCoder 仓库当前仅有研究文档，无任何可运行代码。迭代 1 是首个代码迭代。项目选择基于 AgentScope 框架组合构建编码代理，而非从零实现。AgentScope 已提供模型接入、工具系统、技能、MCP、认证等核心能力。

## Goals / Non-Goals

**Goals:**
- 建立可导入的 `hicoder` 包结构，依赖 `agentscope` 框架
- 实现三层配置加载（内置默认 → 用户配置 → 项目配置），后层覆盖前层
- 基于 AgentScope `Credential` 体系完成 API Key 解析（环境变量优先）
- 配置缺失或无效时给出明确的错误信息
- 配置对象可无缝对接 AgentScope 的模型初始化

**Non-Goals:**
- 不自建模型调用逻辑（AgentScope `model` 模块已覆盖）
- 不自建工具系统（AgentScope `Toolkit` 已内置 shell/read/write/edit/grep）
- 不实现配置热重载
- 不重复实现认证逻辑（AgentScope `credential` 模块已支持 OpenAI/Anthropic）

## Decisions

1. **依赖 AgentScope 而非从零构建**
   - AgentScope 已实现：模型接入（OpenAI/Anthropic）、Toolkit 工具系统、技能加载、MCP 客户端、Credential 认证
   - HiCoder 的定位是在 AgentScope 之上组合出 Codex 风格的产品（CLI + 审批流 + 会话管理）
   - 备选：自建所有模块 → 放弃，重复造轮子且维护成本高

2. **配置使用 tomllib + pydantic BaseModel**
   - AgentScope 自身用 pydantic 做数据验证，HiCoder 配置系统沿用同一技术栈
   - tomllib（Python 3.11+ 标准库）负责 TOML 解析，零额外依赖
   - 浅合并策略：配置结构简单，无需深度嵌套合并

3. **API Key 解析复用 AgentScope Credential**
   - AgentScope 的 `OpenAICredential`、`AnthropicCredential` 已处理环境变量读取逻辑
   - HiCoder 的 `resolve_api_key` 直接调用 Credential 工厂方法，不重复实现
   - 环境变量优先级：环境变量 > 配置文件 > 不设置时报错

4. **配置对象对接 AgentScope 模型初始化**
   - `Config.provider` + `Config.model` 可直接映射到 AgentScope 的模型创建
   - `Config.api_key` 通过 Credential 注入，保持与 AgentScope 一致

5. **项目名 `hicoder`，包名 `hicoder`**
   - CLI 入口后续定义为 `hicoder`
   - 配置目录用 `.hicoder/` 而非 `.codex/`

## Risks / Trade-offs

- [AgentScope API 变更导致 HiCoder 不兼容] → 锁定 agentscope 版本范围（如 `>=1.0.0,<2.0.0`），迭代时关注上游变更
- [浅合并可能导致嵌套配置丢失] → 当前配置结构扁平，无深层嵌套
- [Credential 模块的环境变量名与预期不同] → 迭代 1 测试时验证 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 是否被正确读取
