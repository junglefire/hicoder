## Context

当前 HiCoder 已具备配置加载（迭代 1）和模型接入（迭代 2），但代理只能在单次模型调用后停止，无法形成"提问 → 推理 → 调工具 → 拿结果 → 继续推理"的闭环。需要实现完整的代理循环。

## Goals / Non-Goals

**Goals:**
- 实现异步 Turn 循环引擎，支持多轮模型调用直到无工具调用
- 支持工具注册表、工具定义生成、并行工具执行
- 实现 Shell/Read/Write/Edit 四个基础工具
- 上下文构建：系统提示 + AGENTS.md + 工具定义 + 对话历史
- Session 类管理完整对话生命周期
- `app.py` 接入完整 agent_loop

**Non-Goals:**
- 审批机制（迭代 6）
- 会话持久化/恢复（迭代 7）
- 技能系统（迭代 8）
- MCP 集成（迭代 9）
- 上下文压缩（迭代 10）

## Decisions

**1. Agent loop 使用 async generator 而非 Session 类的 turn 方法**
Agent loop 作为独立异步生成器函数 `agent_loop()`，yield 事件到 UI 层。这样 UI 层（app.py）保持简单，只需遍历事件即可。Session 类负责维护状态，但不直接控制流程。

**2. 工具定义由注册表自动生成 JSON Schema**
每个工具函数使用 `@tool` 装饰器注册，注册表自动生成 OpenAI/Anthropic 兼容的 tool definition（JSON Schema）。避免手动维护 schema。

**3. 工具执行结果通过 ToolCallDone + TextDelta 事件返回**
工具执行结果包装为 AgentMessage(role="tool")，追加到对话历史。工具执行过程的事件（ToolResult）yield 给 UI 层展示。

**4. 上下文构建使用消息列表拼装**
系统提示 + AGENTS.md 指令作为 system 消息，工具定义作为 `tools` 参数传入 model，对话历史按顺序追加。不在消息中硬编码工具定义（浪费 token）。

**5. Shell 工具使用 asyncio.create_subprocess_exec**
使用 Python 标准库 asyncio subprocess，不引入额外依赖。支持超时控制、stdout/stderr 异步读取。

## Risks / Trade-offs

- **[长工具输出截断]** → 实现输出大小限制，超过阈值时截断并附加提示
- **[模型流式响应中的工具调用解析]** → AgentScope 的 ChatResponse 中 ToolCallBlock 在流式模式下可能不完整，需在非流式模式下处理，或取最后一个完整 chunk
- **[工具并发执行的安全]** → Shell 工具需限制工作目录、超时时间，防止无限循环或资源耗尽
