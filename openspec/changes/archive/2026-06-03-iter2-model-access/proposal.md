## Why

迭代 1 已完成配置加载和 API Key 解析，但尚不能向模型发送请求。迭代 2 需要建立模型接入层，使代理能调用 OpenAI 和 Anthropic API 并流式接收回复，为迭代 3 的代理循环奠定基础。

## What Changes

- 基于 AgentScope `ChatModelBase` 创建模型实例，传入迭代 1 的 Config 和 Credential
- 实现统一的流式事件接口，屏蔽 OpenAI 和 Anthropic 的响应差异
- 定义核心事件类型：TextDelta、ToolCall、ToolCallDone、TurnComplete、Error
- 支持模型参数控制（temperature、max_tokens、reasoning_effort）
- Token 用量统计和展示
- 基于 AgentScope 内置重试逻辑的容错处理

## Capabilities

### New Capabilities

- `model-client`: 模型实例化、流式调用、统一事件接口，基于 AgentScope ChatModelBase
- `event-protocol`: 代理事件枚举（TextDelta、ToolCall、TurnComplete 等）
- `message-adapter`: HiCoder 消息格式与 AgentScope Msg 格式之间的转换

### Modified Capabilities

- 无

## Impact

- 新增 `hicoder/models/` 模块（model_client、events、adapter）
- 新增 `hicoder/protocol/` 模块（events.py、models.py）
- Config 模块扩展：新增 temperature、reasoning_effort 等参数字段
- AgentScope 已提供：openai/anthropic SDK、重试逻辑、token 统计，无需额外依赖
