## 1. 事件协议（event-protocol spec）

- [x] 1.1 定义 `AgentEvent` 基类和核心事件 dataclass：TextDelta、ToolCall、ToolCallDone、TurnComplete、Error
- [x] 1.2 定义 `TokenUsage` dataclass（prompt_tokens、completion_tokens、total_tokens）
- [x] 1.3 定义 `AgentMessage` dataclass（role + content 列表，用于内部消息表示）

## 2. 消息适配器（message-adapter spec）

- [x] 2.1 实现 `to_agentscope_messages(messages: list[AgentMessage]) -> list[Msg]` 转换函数
- [x] 2.2 实现 `from_chat_response(response: ChatResponse) -> list[AgentEvent]` 转换函数
- [x] 2.3 实现 `create_tool_result(tool_call_id, output_text) -> Msg` 工具结果消息创建
- [x] 2.4 编写转换测试：用户消息 → Msg、多轮对话 → Msg 列表、ChatResponse → TextDelta/ToolCall

## 3. 模型客户端（model-client spec）

- [x] 3.1 定义 `ModelParams` dataclass（temperature、max_tokens、top_p、reasoning_effort）
- [x] 3.2 实现 `ModelClient` 类：从 Config + Credential 创建 AgentScope 模型实例
- [x] 3.3 实现 `stream(messages) -> AsyncGenerator[AgentEvent, None]` 统一流式接口
- [x] 3.4 实现 AgentScope ChatResponse → HiCoder AgentEvent 转换循环
- [x] 3.5 验证 AgentScope 内置重试逻辑（max_retries=3）已生效
- [x] 3.6 编写集成测试：OpenAI 模型流式调用（mock）、Token 用量正确提取
