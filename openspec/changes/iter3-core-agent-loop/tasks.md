## 1. 工具注册表与定义

- [x] 1.1 创建 `hicoder/tools/__init__.py`，导出 ToolRegistry
- [x] 1.2 创建 `hicoder/tools/registry.py`，实现 `@tool` 装饰器和 ToolRegistry 类
- [x] 1.3 实现 `ToolRegistry.get_tool_definitions()` 自动生成 JSON Schema 定义
- [x] 1.4 实现 `ToolRegistry.execute(name, args)` 执行已注册的工具
- [x] 1.5 实现 `parallel_execute(tool_calls)` 使用 asyncio.gather 并发执行

## 2. 基础工具实现

- [x] 2.1 创建 `hicoder/tools/shell.py`，实现 shell 命令执行工具
- [x] 2.2 创建 `hicoder/tools/file.py`，实现 read_file / write_file / edit_file 工具
- [x] 2.3 创建 `hicoder/tools/truncation.py`，实现输出截断逻辑
- [x] 2.4 在 file 工具中集成 turn diff tracking：write_file/edit_file 成功后生成 unified diff 事件

## 3. Session 与上下文构建

- [x] 3.1 创建 `hicoder/session.py`，实现 Session 类（消息历史、工具注册表、配置）
- [x] 3.2 实现 `Session.receive_user_message()` 和 `Session.get_history()`
- [x] 3.3 实现工具结果格式化：tool_call_id + 输出内容 → AgentMessage(role="tool")
- [x] 3.4 创建上下文构建函数：系统提示 + AGENTS.md + 工具定义 + 历史 → model 输入

## 4. Agent Loop 核心引擎

- [x] 4.1 创建 `hicoder/agent_loop.py`，实现 `agent_loop()` 异步生成器
- [x] 4.2 实现主循环：调用模型 → 解析工具调用 → 并行执行 → 返回结果 → 重复
- [x] 4.3 实现最大 turn 限制（默认 50）
- [x] 4.4 实现取消支持（asyncio.Event）
- [x] 4.5 实现错误处理：工具执行异常 → Error 事件 + 继续循环
- [x] 4.6 实现重试逻辑：区分可重试错误（网络超时、rate limit、5xx）与不可重试错误，可重试错误指数退避重试（1s/2s/4s，最多 3 次）
- [x] 4.7 实现 pending input queue（asyncio.Queue），model 调用间隙 drain 用户新输入并追加到历史
- [x] 4.8 实现 token usage 累计：从 ChatResponse.usage 提取 token 计数，TurnComplete 事件包含总量

## 5. Model Client 扩展

- [x] 5.1 扩展 `model_client.py` 的 `stream()` 方法，将 tools 参数传递给 AgentScope 模型
- [x] 5.2 透传 AgentScope AgentEvent：将模型流式输出转换为 AgentScope 事件类型（TextBlockDelta、ToolCallStart/Delta/End、ModelCallStart/End 等）

## 6. 配置更新

- [x] 6.1 在 `config.py` 的 Config 中添加 `cwd: Path` 字段
- [x] 6.2 在 `config/default.json` 中添加 cwd 默认值

## 7. CLI 集成

- [x] 7.1 修改 `app.py` 的 `_chat_loop`，使用 agent_loop 替代直接调用 model
- [x] 7.2 在 chat 命令中创建 Session 并传入 agent_loop
- [x] 7.3 更新事件处理：支持 ToolResult 等新事件类型的终端输出

## 8. 测试

- [x] 8.1 编写工具注册表的单元测试
- [x] 8.2 编写 shell 和 file 工具的单元测试
- [x] 8.3 编写 agent_loop 的集成测试（含重试、取消、pending input 场景）
- [x] 8.4 编写 turn diff tracking 的单元测试
- [x] 8.5 运行全部现有测试确保无回归
