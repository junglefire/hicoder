# Codex 功能清单与源码映射

> 本清单将每个功能映射到 codex 仓库中对应的实际模块和文件，方便 Python 重写时对照参考。
> 所有路径均相对于 `codex-rs/` 目录。

---

## 一、核心代理引擎（Core Agent Engine）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 1.1 | **Session 初始化** | `core/src/session/session.rs` | `Session` struct, `SessionConfiguration`, `SessionServices` |
| 1.1 | | `core/src/codex_thread.rs` | `CodexThread`, `ThreadConfigSnapshot`, `CodexThreadSettingsOverrides` |
| 1.1 | | `core/src/config/mod.rs` | `Config`, `ConfigBuilder` |
| 1.2 | **Turn 轮次引擎** | `core/src/session/turn.rs` | turn 执行主循环：构建上下文 → 调模型 → 解析/分发工具 → 收集结果 |
| 1.2 | | `core/src/session/handlers.rs` | `user_input_or_turn()`, 处理 `Op` 类型分发 |
| 1.2 | | `core/src/session/mod.rs` | `Session` 的 `submit()` 入口 |
| 1.3 | **流式响应处理** | `core/src/client.rs` | `ModelClient`, `ModelClientSession`, SSE/WebSocket 流 |
| 1.3 | | `core/src/event_mapping.rs` | `parse_turn_item()` — 将模型事件转为 TurnItem |
| 1.3 | | `core/src/stream_events_utils.rs` | `handle_output_item_done()`, `finalize_non_tool_response_item()` |
| 1.4 | **并行工具调用** | `core/src/tools/parallel.rs` | `ToolCallRuntime` — 多工具并发执行 |
| 1.4 | | `core/src/tools/registry.rs` | `AnyToolResult`, `CoreToolRuntime` trait |
| 1.4 | | `core/src/tools/router.rs` | `ToolRouter` — 工具分发路由 |
| 1.5 | **上下文构建** | `core/src/context/mod.rs` | `ContextualUserFragment` trait, 各类上下文片段 |
| 1.5 | | `core/src/context/fragments.rs` | 技能/插件/权限等指令片段组装 |
| 1.5 | | `protocol/src/prompts/base_instructions/` | 基础指令模板（`default.md`） |
| 1.5 | | `core/src/session_prefix.rs` | 会话前缀指令注入 |
| 1.6 | **上下文压缩（本地）** | `core/src/compact.rs` | `run_inline_auto_compact_task()`, `SUMMARIZATION_PROMPT` |
| 1.6 | **上下文压缩（远程 v1）** | `core/src/compact_remote.rs` | `run_inline_remote_auto_compact_task()` |
| 1.6 | **上下文压缩（远程 v2）** | `core/src/compact_remote_v2.rs` | v2 版本远程压缩 |
| 1.6 | | `core/src/client.rs` | `ApiCompactClient`, `CompactionInput` |
| 1.7 | **中断/取消** | `core/src/session/handlers.rs` | `interrupt()`, `clean_background_terminals()` |
| 1.7 | | `core/src/session/input_queue.rs` | `InputQueue` — 用户输入队列，支持中断 |
| 1.7 | | `core/src/state/mod.rs` | `ActiveTurn` — 活动 turn 状态，含取消逻辑 |
| 1.8 | **重试与容错** | `core/src/responses_retry.rs` | `handle_retryable_response_stream_error()`, 退避重试 |
| 1.8 | | `core/src/util.rs` | `backoff()` — 指数退避 |

---

## 二、模型接入（Model Providers）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 2.1 | **OpenAI Responses API** | `core/src/client.rs` | `ModelClient::stream()`, `ResponsesApiRequest`, WebSocket/SSE |
| 2.1 | | `codex-api/src/lib.rs` | `ResponsesClient`, `ResponsesWebsocketClient`, `SseTelemetry` |
| 2.1 | | `responses-api-proxy/src/lib.rs` | Responses API 代理/转发 |
| 2.2 | **OpenAI Chat Completions** | `codex-api/src/amazon_bedrock/` | 备用 API 客户端实现 |
| 2.3 | **Anthropic Messages API** | `model-provider/src/provider.rs` | 多提供商 provider 创建（含 Anthropic） |
| 2.3 | | `model-provider-info/src/lib.rs` | `ModelProviderInfo`, 内置提供商列表 |
| 2.4 | **模型参数控制** | `protocol/src/openai_models.rs` | `ReasoningEffort`, `ModelInfo` |
| 2.4 | | `protocol/src/config_types.rs` | `ServiceTier`, `ReasoningSummary` |
| 2.4 | | `core/src/client.rs` | `reasoning_effort`, `service_tier` 传递 |
| 2.5 | **模型切换** | `models-manager/src/` | `ModelsManager`, `SharedModelsManager` |
| 2.5 | | `core/src/thread_manager.rs` | `build_models_manager()` |
| 2.6 | **Token 用量统计** | `protocol/src/protocol.rs` | `TokenCountEvent`, `TokenUsageInfo` |
| 2.6 | | `otel/src/metrics.rs` | Token 用量指标上报 |

---

## 三、工具系统（Tool System）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 3.1 | **工具注册表** | `tools/src/tool_definition.rs` | `ToolDefinition` — 名称/描述/JSON Schema |
| 3.1 | | `tools/src/tool_spec.rs` | `ToolSpec` — 向模型暴露的工具规格 |
| 3.1 | | `tools/src/tool_discovery.rs` | 工具发现与注册 |
| 3.1 | | `core/src/tools/registry.rs` | `CoreToolRuntime` trait, `ToolRouter` |
| 3.2 | **Shell 命令执行** | `core/src/exec.rs` | 命令执行主逻辑：spawn、读输出、超时、退出码 |
| 3.2 | | `core/src/spawn.rs` | `spawn_child_async()` — 异步子进程启动 |
| 3.2 | | `exec-server/src/server.rs` | 执行服务器 |
| 3.2 | | `exec-server/src/process.rs` | 进程管理接口 |
| 3.3 | **文件读取（Read）** | `core/src/agent/builtins/` | 内置 Read 工具 |
| 3.4 | **文件写入（Write）** | `core/src/agent/builtins/` | 内置 Write 工具 |
| 3.5 | **代码补丁（apply_patch）** | `core/src/apply_patch.rs` | `apply_patch()` — diff 应用与冲突检测 |
| 3.5 | | `apply-patch/src/lib.rs` | 补丁解析与应用核心逻辑 |
| 3.6 | **编辑（Edit）** | `core/src/config/edit.rs` | 配置编辑功能 |
| 3.6 | | `core/src/agent/builtins/` | 内置 Edit 工具 |
| 3.7 | **文件搜索（Find/Grep）** | `file-search/src/lib.rs` | 文件搜索实现 |
| 3.7 | | `core/src/agent/builtins/` | 内置 Grep/Find 工具 |
| 3.8 | **后台终端** | `core/src/unified_exec/` | 统一执行管理，后台终端超时 |
| 3.8 | | `exec-server/src/runtime.rs` | 运行时进程管理 |
| 3.9 | **MCP 工具** | `codex-mcp/src/` | MCP 工具连接与调用 |
| 3.9 | | `core/src/mcp_tool_call.rs` | MCP 工具调用处理 |
| 3.9 | | `core/src/mcp.rs` | `McpManager` — MCP 管理器 |
| 3.10 | **工具输出截断** | `utils/output-truncation/src/lib.rs` | `TruncationPolicy`, `truncate_text()` |
| 3.10 | | `core/src/agent/mod.rs` | `format_exec_output_for_model()`, 截断常量 |
| 3.11 | **工具结果格式化** | `core/src/agent/mod.rs` | `format_exec_output_str()`, `build_content_with_timeout()` |
| 3.11 | | `protocol/src/exec_output.rs` | `ExecToolCallOutput`, `StreamOutput` |

---

## 四、审批与安全（Approval & Security）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 4.1 | **执行策略（exec_policy）** | `core/src/exec_policy.rs` | `load_exec_policy()`, `check_execpolicy_for_warnings()`, 规则评估 |
| 4.1 | | `execpolicy/src/lib.rs` | `Policy`, `PolicyParser`, `Decision`, `RuleMatch` |
| 4.1 | | `execpolicy-legacy/` | 旧版执行策略解析器 |
| 4.2 | **命令审批** | `protocol/src/approvals.rs` | `ExecApprovalRequestEvent`, `ExecApprovalResponse` |
| 4.2 | | `core/src/tools/sandboxing.rs` | `ExecApprovalRequirement`, 权限请求 |
| 4.2 | | `core/src/session/handlers.rs` | `ExecApproval` 操作处理 |
| 4.3 | **补丁审批** | `protocol/src/approvals.rs` | `ApplyPatchApprovalRequestEvent`, `PatchApprovalResponse` |
| 4.3 | | `core/src/session/review.rs` | 审查流程 |
| 4.4 | **权限持久化** | `execpolicy/src/lib.rs` | `blocking_append_allow_prefix_rule()` — 追加允许规则 |
| 4.4 | | `protocol/src/approvals.rs` | `ExecPolicyAmendment` — 策略修正案 |
| 4.5 | **文件系统权限** | `protocol/src/permissions.rs` | `FileSystemSandboxPolicy`, `WritableRoot`, 保护路径 |
| 4.5 | | `protocol/src/models.rs` | `PermissionProfile`, `ActivePermissionProfile` |
| 4.6 | **网络策略** | `protocol/src/network_policy.rs` | `NetworkPolicyDecisionPayload` |
| 4.6 | | `network-proxy/src/lib.rs` | `NetworkProxy`, 代理配置 |
| 4.6 | | `core/src/network_policy_decision.rs` | 网络策略决策评估 |
| 4.7 | **沙箱策略（简化）** | `sandboxing/src/manager.rs` | `SandboxManager`, `SandboxTransformRequest`, `SandboxType` |
| 4.7 | | `sandboxing/src/seatbelt.rs` | macOS Seatbelt 策略生成 |
| 4.7 | | `sandboxing/src/landlock.rs` | Linux 沙箱命令构建 |
| 4.7 | | `sandboxing/src/policy_transforms.rs` | 权限配置到沙箱策略的转换 |
| 4.7 | | `linux-sandbox/src/main.rs` | Linux 沙箱辅助进程 |
| 4.7 | | `bwrap/src/bwrap.rs` | Bubblewrap 封装 |

---

## 五、会话管理（Session Management）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 5.1 | **会话持久化** | `rollout/src/lib.rs` | `RolloutRecorder`, `RolloutRecorderParams` |
| 5.1 | | `core/src/rollout.rs` | `RolloutRecorder` 的 ConfigView 实现 |
| 5.2 | **会话恢复** | `core/src/session/rollout_reconstruction.rs` | `reconstruct_history_from_rollout()`, `RolloutReconstruction` |
| 5.2 | | `thread-store/src/store.rs` | `LocalThreadStore`, `ReadThreadParams` |
| 5.3 | **会话元数据** | `thread-store/src/types.rs` | `StoredThread`, `ThreadMetadataPatch` |
| 5.3 | | `rollout/src/lib.rs` | `SessionMeta`, `ThreadItem` |
| 5.4 | **会话归档** | `rollout/src/lib.rs` | `ARCHIVED_SESSIONS_SUBDIR`, `SESSIONS_SUBDIR` |
| 5.4 | | `core/src/rollout.rs` | `find_archived_thread_path_by_id_str()` |
| 5.5 | **会话 Fork** | `core/src/thread_manager.rs` | `ForkSnapshot`, `NewThread`, `StartThreadOptions` |
| 5.5 | | `core/src/codex_thread.rs` | `parent_thread_id`, 线程 fork 配置 |

---

## 六、配置系统（Config System）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 6.1 | **config.toml 加载** | `core/src/config/mod.rs` | `Config`, `ConfigBuilder`, 层栈加载 |
| 6.1 | | `core/src/config/config_loader.rs` | 配置文件解析与合并 |
| 6.1 | | `config/src/loader.rs` | `load_config_layers_state()`, 层栈排序 |
| 6.2 | **模型配置** | `model-provider-info/src/lib.rs` | `ModelProviderInfo`, `built_in_model_providers()` |
| 6.2 | | `model-provider/src/provider.rs` | `create_model_provider()` |
| 6.3 | **审批策略配置** | `core/src/config/permissions.rs` | 审批策略 TOML 解析 |
| 6.3 | | `protocol/src/config_types.rs` | `AskForApproval`, `ApprovalsReviewer` |
| 6.4 | **沙箱模式配置** | `protocol/src/config_types.rs` | `SandboxMode` |
| 6.4 | | `core/src/config/resolved_permission_profile.rs` | 权限配置解析 |
| 6.5 | **MCP 服务器配置** | `config/src/types.rs` | `McpServerConfig`, `McpServerTransportConfig` |
| 6.5 | | `core/src/mcp.rs` | `McpManager::configured_servers()` |
| 6.6 | **网络代理** | `core/src/config/network_proxy_spec.rs` | 网络代理配置规范 |
| 6.6 | | `network-proxy/src/lib.rs` | `NetworkProxy`, 环境变量传递 |
| 6.7 | **功能开关** | `features/src/lib.rs` | `Feature`, `FeatureToml`, `FeatureOverrides` |
| 6.7 | | `core/src/config/managed_features.rs` | 会话内功能开关管理 |

---

## 七、技能系统（Skills）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 7.1 | **技能目录扫描** | `skills/src/lib.rs` | `install_system_skills()`, 嵌入式技能安装 |
| 7.1 | | `core-skills/src/loader.rs` | 技能加载：系统/用户/仓库/插件四级 |
| 7.1 | | `core-skills/src/manager.rs` | `SkillsManager`, `SkillsLoadInput` |
| 7.2 | **技能指令注入** | `core-skills/src/injection.rs` | `build_skill_injections()`, `SkillInjections` |
| 7.2 | | `core/src/skills.rs` | `skills_load_input_from_config()` |
| 7.2 | | `core/src/context/skill_instructions.rs` | 技能指令上下文片段 |
| 7.3 | **显式技能调用** | `core-skills/src/injection.rs` | `collect_explicit_skill_mentions()` — 解析 `@skill` |
| 7.4 | **隐式技能调用** | `core-skills/src/invocation_utils.rs` | `detect_implicit_skill_invocation_for_command()` |
| 7.4 | | `core/src/skills.rs` | `maybe_emit_implicit_skill_invocation()` |
| 7.5 | **技能作用域** | `core-skills/src/model.rs` | `SkillPolicy` — System/User/Repo/Admin |
| 7.5 | | `core-skills/src/render.rs` | `AvailableSkills`, `SkillRenderReport` |

---

## 八、钩子系统（Hooks）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 8.1 | **Pre-tool-use 钩子** | `core/src/hook_runtime.rs` | `run_pre_tool_use_hooks()`, `PreToolUseHookResult` |
| 8.1 | | `hooks/src/lib.rs` | `PreToolUseRequest`, `PreToolUseOutcome` |
| 8.2 | **Post-tool-use 钩子** | `core/src/hook_runtime.rs` | `run_post_tool_use_hooks()` |
| 8.2 | | `hooks/src/lib.rs` | `PostToolUseRequest`, `PostToolUseOutcome` |
| 8.3 | **Session-start 钩子** | `core/src/hook_runtime.rs` | `run_pending_session_start_hooks()` |
| 8.3 | | `hooks/src/lib.rs` | `SessionStartOutcome`, `StartHookTarget` |
| 8.4 | **Turn-stop 钩子** | `core/src/hook_runtime.rs` | `run_turn_stop_hooks()` |
| 8.4 | | `hooks/src/lib.rs` | `StopOutcome`, `StopHookTarget` |
| 8.5 | **After-agent 钩子** | `core/src/hook_runtime.rs` | `run_legacy_after_agent_hook()` |
| 8.5 | | `core/src/tools/hook_names.rs` | `HookToolName` — 钩子工具名称枚举 |

---

## 九、MCP 支持

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 9.1 | **MCP 客户端** | `codex-mcp/src/mcp_connection_manager.rs` | MCP 连接管理、工具发现 |
| 9.1 | | `core/src/mcp.rs` | `McpManager` — MCP 管理器 |
| 9.1 | | `rmcp-client/src/` | RMCP（Rust MCP）客户端实现 |
| 9.2 | **MCP 工具调用** | `core/src/mcp_tool_call.rs` | MCP 工具调用执行与结果处理 |
| 9.2 | | `core/src/mcp_tool_exposure.rs` | MCP 工具向模型的暴露控制 |
| 9.2 | | `core/src/mcp_skill_dependencies.rs` | MCP 依赖安装提示 |
| 9.3 | **MCP OAuth 认证** | `codex-mcp/src/` | MCP OAuth 凭据存储与认证 |
| 9.3 | | `config/src/types.rs` | `McpOAuthCredentialsStoreMode` |
| 9.4 | **MCP 服务器模式** | `mcp-server/src/main.rs` | `run_main()` — MCP 服务器入口 |
| 9.4 | | `mcp-server/src/message_processor.rs` | MCP 消息处理 |
| 9.4 | | `mcp-server/src/codex_tool_runner.rs` | `codex` 工具实现 |
| 9.5 | **MCP 生命周期** | `core/src/session/mcp.rs` | MCP 启动状态追踪与告警 |
| 9.5 | | `protocol/src/protocol.rs` | `McpStartupUpdateEvent`, `McpStartupCompleteEvent` |

---

## 十、多代理（Multi-Agent）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 10.1 | **子代理生成** | `core/src/thread_manager.rs` | `NewThread`, `StartThreadOptions`, 线程生成 |
| 10.1 | | `core/src/session/multi_agents.rs` | 多代理使用提示文本 |
| 10.2 | **代理间通信** | `protocol/src/protocol.rs` | `Op::InterAgentCommunication`, `InterAgentCommunication` |
| 10.2 | | `core/src/session/handlers.rs` | `InterAgentCommunication` 处理 |
| 10.3 | **嵌套深度限制** | `core/src/agent/registry.rs` | `exceeds_thread_spawn_depth_limit()`, `next_thread_spawn_depth()` |
| 10.4 | **独立上下文** | `core/src/codex_thread.rs` | 每个 `CodexThread` 有独立 `Session` 和事件通道 |
| 10.4 | | `core/src/agent/role.rs` | 代理角色配置层（`apply_role_to_config()`） |
| 10.4 | | `core/src/agent/control.rs` | `AgentControl` — 代理控制 |
| 10.4 | | `core/src/agent/status.rs` | `AgentStatus` — 代理状态 |
| 10.4 | | `core/src/goals.rs` | `GoalRuntimeState` — 跨轮次目标跟踪 |

---

## 十一、扩展与插件（Extensions & Plugins）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 11.1 | **插件发现** | `core/src/plugins/discoverable.rs` | 插件扫描与注册 |
| 11.1 | | `core/src/plugins/mentions.rs` | 插件提及解析 |
| 11.1 | | `core/src/plugins/render.rs` | 插件指令渲染 |
| 11.2 | **插件工具注册** | `ext/extension-api/src/lib.rs` | `ToolCallOutcome`, 扩展工具接口 |
| 11.2 | | `plugin/src/lib.rs` | `PluginsManager` |
| 11.3 | **插件指令注入** | `core/src/plugins/injection.rs` | `build_plugin_injections()` |
| 11.3 | | `core/src/context/plugin_instructions.rs` | 插件指令上下文片段 |
| 11.4 | **插件提及解析** | `core/src/plugins/mentions.rs` | `collect_explicit_plugin_mentions()` — 解析 `@plugin` |

---

## 十二、记忆系统（Memory）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 12.1 | **持久化记忆** | `memories/write/src/runtime.rs` | 记忆写入 |
| 12.1 | | `memories/read/src/runtime.rs` | 记忆读取 |
| 12.2 | **跨会话保留** | `memories/write/src/storage.rs` | SQLite 存储，跨会话持久化 |
| 12.3 | **记忆注入** | `ext/memories/src/extension.rs` | 记忆扩展注入 |
| 12.3 | | `memories/read/src/prompts.rs` | 记忆提示词构建 |
| 12.3 | | `core/src/client.rs` | `ApiMemoriesClient`, `MemorySummarizeInput` |
| 12.3 | | `protocol/src/memory_citation.rs` | `MemoryCitation` — 记忆引用 |

---

## 十三、用户交互（CLI）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 13.1 | **交互式 REPL** | `tui/src/app.rs` | `App` — TUI 主循环（Python 版可简化为 readline 交互） |
| 13.1 | | `tui/src/bottom_pane/mod.rs` | 底部输入面板 |
| 13.2 | **非交互模式（exec）** | `exec/src/main.rs` | `codex exec` 入口 |
| 13.2 | | `exec/src/event_processor.rs` | 事件处理与输出格式化 |
| 13.2 | | `exec/src/event_processor_with_human_output.rs` | 人类可读输出 |
| 13.2 | | `exec/src/event_processor_with_jsonl_output.rs` | JSONL 输出 |
| 13.3 | **流式输出展示** | `tui/src/streaming/` | 流式 Markdown 渲染 |
| 13.3 | | `tui/src/markdown_render.rs` | `pulldown-cmark` + `syntect` 语法高亮 |
| 13.3 | | `tui/src/history_cell/` | 不同类型消息的渲染 |
| 13.4 | **审批交互** | `tui/src/bottom_pane/mod.rs` | 审批请求 UI |
| 13.4 | | `protocol/src/protocol.rs` | `ExecApprovalRequestEvent`, `ApplyPatchApprovalRequestEvent` |
| 13.5 | **会话选择** | `tui/src/resume_picker.rs` | `SessionSelection`, 历史会话浏览 |
| 13.5 | | `core/src/rollout.rs` | `find_thread_path_by_id_str()`, 会话列表 |
| 13.6 | **斜杠命令** | `tui/src/slash_command.rs` | 斜杠命令解析与分发 |
| 13.7 | **Markdown 渲染** | `tui/src/markdown_render.rs` | Markdown 解析与高亮 |
| 13.7 | | `tui/src/render/highlight.rs` | `highlight_bash_to_lines()` |

---

## 十四、认证（Authentication）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 14.1 | **OpenAI API Key** | `login/src/auth_env_telemetry.rs` | 环境变量认证 |
| 14.1 | | `model-provider-info/src/read_api_key.rs` | API Key 读取 |
| 14.2 | **Anthropic API Key** | `model-provider/src/provider.rs` | Anthropic provider 认证 |
| 14.3 | **Keyring 存储** | `keyring-store/src/lib.rs` | 系统密钥环读写 |
| 14.3 | | `login/src/lib.rs` | `AuthManager`, `CodexAuth` |
| 14.3 | | `login/src/device_code_auth.rs` | Device Code 认证流程 |
| 14.3 | | `login/src/pkce.rs` | PKCE OAuth 流程 |
| 14.3 | | `login/src/token_data.rs` | Token 管理与刷新 |

---

## 十五、可观测性（Observability）

| # | 功能 | 对应模块/文件 | 关键结构/函数 |
|---|------|-------------|-------------|
| 15.1 | **日志系统** | `otel/src/lib.rs` | OpenTelemetry 集成 |
| 15.1 | | `otel/src/provider.rs` | 日志 provider |
| 15.1 | | `otel/src/trace_context.rs` | W3C Trace Context 传播 |
| 15.2 | **Token 统计** | `otel/src/metrics.rs` | Token 用量指标 |
| 15.2 | | `analytics/src/events.rs` | 分析事件上报 |
| 15.2 | | `protocol/src/protocol.rs` | `TokenCountEvent` |
| 15.3 | **性能指标** | `otel/src/metrics.rs` | TTFT、工具执行耗时等 |
| 15.3 | | `analytics/src/facts.rs` | 事实数据收集 |
| 15.3 | | `core/src/turn_timing.rs` | TTFT（首次 token 时间）记录 |
| 15.3 | | `core/src/turn_metadata.rs` | Turn 级元数据（含耗时） |

---

## 附录：核心协议类型速查

### Op（请求类型）
| Op 变体 | 文件 | 说明 |
|---------|------|------|
| `Op::Interrupt` | `protocol/src/protocol.rs:498` | 中断当前 turn |
| `Op::UserInput` | `protocol/src/protocol.rs` | 用户输入 |
| `Op::ExecApproval` | `protocol/src/protocol.rs` | 命令审批响应 |
| `Op::PatchApproval` | `protocol/src/protocol.rs` | 补丁审批响应 |
| `Op::ResolveElicitation` | `protocol/src/protocol.rs` | MCP elicitation 响应 |
| `Op::UserInputAnswer` | `protocol/src/protocol.rs` | request_user_input 响应 |
| `Op::RequestPermissionsResponse` | `protocol/src/protocol.rs` | 权限请求响应 |
| `Op::ThreadSettings` | `protocol/src/protocol.rs` | 线程设置修改 |
| `Op::InterAgentCommunication` | `protocol/src/protocol.rs` | 代理间通信 |

### EventMsg（事件类型）
| EventMsg 变体 | 文件 | 说明 |
|---------------|------|------|
| `TurnStarted` | `protocol/src/protocol.rs:1198` | Turn 开始 |
| `TurnComplete` | `protocol/src/protocol.rs:1207` | Turn 完成 |
| `TurnAborted` | `protocol/src/protocol.rs:1308` | Turn 中止 |
| `AgentMessage` | `protocol/src/protocol.rs:1214` | 代理文本输出 |
| `AgentReasoning` | `protocol/src/protocol.rs:1220` | 推理内容 |
| `ExecCommandBegin/End` | `protocol/src/protocol.rs` | 命令执行生命周期 |
| `PatchApplyBegin/End` | `protocol/src/protocol.rs` | 补丁应用生命周期 |
| `ExecApprovalRequest` | `protocol/src/protocol.rs` | 命令审批请求 |
| `McpToolCallBegin/End` | `protocol/src/protocol.rs` | MCP 工具调用生命周期 |
| `ContextCompacted` | `protocol/src/protocol.rs:1190` | 上下文已压缩 |
| `Error/Warning` | `protocol/src/protocol.rs` | 错误/警告 |

---

*文档生成时间：2026-06-02*
*基于 codex 仓库最新代码分析，所有路径相对于 `codex-rs/`*
