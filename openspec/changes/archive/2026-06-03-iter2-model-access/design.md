## Context

迭代 1 已完成 Config 和 Credential 系统。HiCoder 需要接入模型调用能力，但 AgentScope 已提供完整的 `OpenAIChatModel`、`AnthropicChatModel` 和 `ChatModelBase` 抽象层。本迭代的核心工作是：将 Config 映射为 AgentScope 模型实例，并定义 HiCoder 自身的统一事件协议。

## Goals / Non-Goals

**Goals:**
- 从 Config 创建 AgentScope 模型实例（provider + model + credential + parameters）
- 统一的流式事件接口：TextDelta、ToolCall、ToolCallDone、TurnComplete、Error
- 支持 temperature、max_tokens 等模型参数
- Token 用量统计在 turn 结束时可用
- 消息格式转换：HiCoder 内部消息 ↔ AgentScope Msg

**Non-Goals:**
- 不实现代理循环（迭代 3）
- 不实现工具执行（迭代 3-4）
- 不实现 CLI 界面（迭代 5）
- 不实现上下文压缩（迭代 10）

## Decisions

1. **直接使用 AgentScope 模型，不做额外封装层**
   - AgentScope `ChatModelBase` 已提供：`__call__` 异步流式调用、重试逻辑、token 估算
   - HiCoder 的 `ModelClient` 仅负责：创建实例 + 将 AgentScope `ChatResponse` 转换为 HiCoder 事件
   - 备选：自建 httpx SSE 客户端 → 放弃，AgentScope 已完整实现且处理了重试/错误

2. **事件协议使用 Python dataclass 而非 pydantic**
   - 事件是瞬时对象（不像 Config 需要验证/序列化），dataclass 更轻量
   - 所有事件继承自 `AgentEvent` 基类，支持 isinstance 模式匹配
   - AgentScope 的 `ChatResponse` 使用 dataclass，保持一致风格

3. **Message 适配器：HiCoder 用简单 dict 列表对接 AgentScope Msg**
   - HiCoder 内部维护轻量级消息格式（role + content）
   - 在调用模型前转换为 AgentScope `Msg` 对象
   - 不做双向完整转换（只需 → Msg 方向），工具结果等后续迭代补充

4. **模型参数使用 pydantic BaseModel 聚合**
   - `ModelParams` dataclass 包含：temperature、max_tokens、top_p、reasoning_effort
   - 创建模型实例时注入到 AgentScope 的 Parameters
   - 后续迭代中可被 `/model` 斜杠命令动态修改

5. **错误事件统一为 Error，不细分类型**
   - 网络错误、API 错误、解析错误统一产出 `Error` 事件
   - CLI 层根据 error.message 展示，不需要类型区分
   - 后续如需细分可按 Error.code 枚举扩展

## Risks / Trade-offs

- [AgentScope 版本升级导致 API 不兼容] → 锁定 agentscope>=2.0.0,<3.0.0，迭代时关注上游变更
- [直接依赖 AgentScope ChatResponse 导致耦合] → 事件转换层(ModelClient) 是隔离点，内部消息格式不暴露 AgentScope 类型
- [AgentScope 流式响应格式可能与文档描述不同] → 先用简单测试验证流式输出，迭代 3 前确保稳定
