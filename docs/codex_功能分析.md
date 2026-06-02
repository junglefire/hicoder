# Codex 项目功能分析

> Codex CLI 是 OpenAI 开源的本地编码代理（coding agent），以 Rust 语言实现，提供零依赖的独立可执行文件。本项目采用 Cargo workspace 架构，包含 100+ 个 crate。

---

## 一、项目概览

| 维度 | 说明 |
|------|------|
| **语言** | Rust 2024 Edition |
| **构建系统** | Bazel + Cargo（双构建系统） |
| **前端 UI** | Ratatui 终端 UI（TUI） |
| **协议** | 自定义 SQ/EQ（Submission Queue / Event Queue）协议 + MCP（Model Context Protocol） |
| **模型接入** | OpenAI Responses API、OpenRouter、Ollama、LMStudio、Gemini、DashScope、Anthropic 等多提供商 |
| **许可证** | Apache-2.0 |
| **安装方式** | npm / Homebrew / 二进制下载 |

---

## 二、核心架构

```
┌─────────────────────────────────────────────────────────┐
│                     CLI 入口层                           │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐  │
│  │  codex    │  │ codex    │  │ codex mcp-server      │  │
│  │  (TUI)    │  │ exec     │  │ (MCP 服务端)           │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬────────────┘  │
│       │              │                   │               │
├───────┼──────────────┼───────────────────┼───────────────┤
│       ▼              ▼                   ▼               │
│  ┌──────────────────────────────────────────────────┐    │
│  │              App Server 层                        │    │
│  │  ┌────────────┐ ┌─────────────┐ ┌─────────────┐  │    │
│  │  │ v1 协议     │ │ v2 协议      │ │ Transport   │  │    │
│  │  └────────────┘ └─────────────┘ └─────────────┘  │    │
│  └────────────────────────┬─────────────────────────┘    │
│                           │                              │
├───────────────────────────┼──────────────────────────────┤
│                           ▼                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Agent 核心层 (codex-core)              │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐  │  │
│  │  │ Session  │ │ Thread   │ │ Turn     │ │Model  │  │  │
│  │  │ 会话管理  │ │ 线程管理  │ │ 轮次执行  │ │ 客户端 │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐  │  │
│  │  │ Tools    │ │ Skills   │ │ MCP      │ │Config │  │  │
│  │  │ 工具系统  │ │ 技能系统  │ │ 客户端    │ │ 配置   │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └───────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                              │
├───────────────────────────┼──────────────────────────────┤
│                    ┌──────┴──────┐                        │
│                    ▼             ▼                        │
│           ┌────────────┐ ┌────────────┐                  │
│           │ Sandbox    │ │ Exec Server│                  │
│           │ 沙箱隔离    │ │ 执行服务器  │                  │
│           └────────────┘ └────────────┘                  │
└──────────────────────────────────────────────────────────┘
```

---

## 三、关键 Crate 分析

### 3.1 codex-core（核心业务逻辑）

项目最大的 crate，承载编码代理的核心逻辑：

| 子模块 | 功能 |
|--------|------|
| `session/` | 会话生命周期管理，包含 Session 初始化、输入队列、配置锁定 |
| `session/turn.rs` | **Turn（轮次）执行引擎**：接收用户输入 → 构建上下文 → 调用模型 → 分发工具调用 → 收集结果 → 返回响应 |
| `session/handlers.rs` | 操作处理器：用户输入、审批响应、MCP 响应、实时音频/文本、审查线程等 |
| `codex_thread.rs` | 线程（Thread）管理：配置快照、设置覆盖、子线程生成 |
| `client.rs` | 模型客户端：与 OpenAI Responses API / SSE 流通信 |
| `compact.rs` | **上下文压缩**：当 token 数接近限制时自动压缩对话历史（本地压缩 + 远程压缩 v2） |
| `config/` | 配置系统：`config.toml` 加载、权限策略、网络代理、MCP 服务器配置、功能开关 |
| `exec_policy.rs` | 执行策略：定义哪些命令可自动执行、哪些需要用户审批 |
| `sandboxing/` | 沙箱策略标签：基于权限配置文件映射到沙箱执行策略 |
| `skills.rs` | 技能系统：加载、渲染、注入技能指令到模型上下文 |
| `mcp.rs` | MCP 工具调用管理：MCP 服务器连接、工具发现、认证 |
| `plugins/` | 插件系统：连接器（connectors）、插件发现与注入 |
| `hook_runtime.rs` | 钩子系统：pre_tool_use / post_tool_use / session_start / turn_stop 等生命周期钩子 |
| `thread_manager.rs` | **线程管理器**：管理多个并行代理线程，支持线程 fork/合并 |
| `rollout.rs` | 会话持久化：将对话历史写入磁盘以便恢复 |
| `agent/` | 多代理系统：代理注册、角色定义、状态管理 |
| `tools/` | 工具注册表与分发：CoreToolRuntime trait、钩子载荷、工具参数 diff 消费者 |
| `realtime_conversation.rs` | 实时对话：支持音频流输入/输出（WebRTC / WebSocket） |
| `guardian/` | 守护者系统：自动审批审查、风险评估、权限评估 |
| `goals/` | 长期目标管理：代理可跟踪跨多个轮次的目标任务 |
| `tasks/` | 后台任务：压缩任务、用户 shell 命令、后台终端管理 |

### 3.2 codex-tui（终端用户界面）

基于 Ratatui 的全屏终端 UI：

| 子模块 | 功能 |
|--------|------|
| `app.rs` | 主应用状态机：协调 ChatWidget、底栏、侧栏等组件 |
| `chatwidget.rs` | 聊天组件：消息渲染、流式输出、推理内容展示 |
| `bottom_pane/` | 底部面板：输入框、审批请求、选择视图、MCP  elicitation 表单 |
| `history_cell/` | 历史记录单元：不同类型消息的渲染（代码块、diff、命令输出、推理等） |
| `exec_cell/` | 命令执行单元：显示命令、输出、退出码、耗时 |
| `streaming/` | 流式渲染处理：markdown 流式解析、语法高亮 |
| `markdown_render/` | Markdown 渲染：pulldown-cmark + syntect 语法高亮 |
| `file_search.rs` | 文件搜索：模糊匹配文件路径（nucleo 引擎） |
| `resume_picker.rs` | 会话恢复选择器：浏览和恢复历史会话 |
| `voice.rs` | 语音交互：实时音频录制和播放 |
| `collaboration_modes.rs` | 协作模式：共享编辑/协作会话 |
| `multi_agents.rs` | 多代理 UI：代理选择器、子代理状态显示 |
| `onboarding/` | 新用户引导流程 |
| `pets/` | UI 宠物（装饰性元素） |
| `theme_picker.rs` | 主题选择器 |

### 3.3 codex-cli（命令行入口）

CLI 多工具入口，提供多种子命令：

| 子命令 | 功能 |
|--------|------|
| `codex` | 启动 TUI 交互模式 |
| `codex exec PROMPT` | 非交互模式：执行单个 prompt 后退出 |
| `codex mcp-server` | 作为 MCP 服务器启动，供其他 MCP 客户端调用 |
| `codex sandbox CMD` | 在沙箱中执行命令（用于测试沙箱行为） |
| `codex app` | 启动桌面应用模式 |

### 3.4 app-server 系列

| Crate | 功能 |
|-------|------|
| `codex-app-server` | 应用服务器主实现：消息处理、请求处理、连接管理 |
| `codex-app-server-protocol` | 协议定义：v1 和 v2 RPC 接口、事件类型、TypeScript 类型导出 |
| `codex-app-server-transport` | 传输层：UDS（Unix Domain Socket）和 stdio 传输 |
| `codex-app-server-client` | 客户端 SDK：供 TUI 连接 app-server |
| `codex-app-server-daemon` | 后台进程管理：app-server 守护进程的启动/连接 |

**app-server v2 协议特性**：
- 采用 `<resource>/<method>` 风格的 RPC 方法命名
- 支持游标分页（cursor pagination）
- 实验性 API 的门控机制（`#[experimental(...)]`）
- 自动生成 TypeScript 类型（ts-rs）

### 3.5 codex-protocol（协议定义）

定义 Codex 内部通信协议：

- **Submission Queue (SQ)**：客户端 → 代理的请求队列
- **Event Queue (EQ)**：代理 → 客户端的事件队列

**Op 枚举（请求类型）**：
- `Interrupt` — 中断当前任务
- `UserInput` — 用户输入（文本/图片/文件）
- `ExecApproval` — 审批命令执行
- `PatchApproval` — 审批代码补丁
- `ResolveElicitation` — 响应 MCP  elicitation 请求
- `UserInputAnswer` — 响应 request_user_input 工具调用
- `RequestPermissionsResponse` — 响应权限请求
- `ThreadSettings` — 修改线程设置
- `RealtimeConversation*` — 实时音频对话控制

**EventMsg 枚举（事件类型）**：50+ 种事件，涵盖：
- 生命周期：TurnStarted / TurnComplete / TurnAborted
- 模型输出：AgentMessage / AgentReasoning / AgentReasoningRawContent
- 工具执行：ExecCommandBegin / ExecCommandOutputDelta / ExecCommandEnd
- 代码操作：PatchApplyBegin / PatchApplyUpdated / PatchApplyEnd
- 审批：ExecApprovalRequest / ApplyPatchApprovalRequest / GuardianAssessment
- MCP：McpToolCallBegin / McpToolCallEnd / McpStartupUpdate
- 搜索与生成：WebSearchBegin / ImageGenerationBegin
- 系统：Error / Warning / ContextCompacted / ModelReroute

### 3.6 codex-tools（工具定义与执行）

| 子模块 | 功能 |
|--------|------|
| `tool_definition.rs` | 工具定义：名称、描述、JSON Schema 输入/输出 |
| `tool_executor.rs` | 工具执行器 trait |
| `tool_spec.rs` | 工具规格：向模型暴露的工具描述 |
| `tool_discovery.rs` | 工具发现机制 |
| `mcp_tool.rs` | MCP 工具适配 |
| `responses_api.rs` | Responses API 工具定义 |
| `code_mode.rs` | 代码模式工具：代码生成/修改专用工具 |
| `request_plugin_install.rs` | 请求插件安装工具 |

### 3.7 codex-sandboxing（沙箱系统）

跨平台沙箱隔离：

| 平台 | 沙箱技术 |
|------|----------|
| macOS | **Seatbelt**（sandbox-exec + SBPL 策略文件） |
| Linux | **Bubblewrap**（bwrap）+ **Landlock**（LSM 文件系统限制） |
| Windows | **Windows Sandbox**（受限 Token + 完整性级别） |

**沙箱策略模式**：
- `read-only` — 只读文件系统，禁止网络
- `workspace-write` — 工作区可写，其他只读
- `danger-full-access` — 无沙箱（仅限隔离环境）
- `network-enabled` — 可配置网络访问策略

### 3.8 codex-skills（技能系统）

技能系统允许项目定义自定义代理行为：

| 组件 | 功能 |
|------|------|
| 系统技能 | 编译时嵌入的内置技能（`skills/src/assets/samples/`） |
| 用户技能 | `~/.codex/skills/` 目录下的自定义技能 |
| 仓库技能 | 项目根目录的 `.codex/skills/` |
| 插件技能 | 通过插件系统加载的技能 |
| 隐式技能调用 | 根据用户命令自动检测并注入相关技能指令 |
| 技能作用域 | System / User / Repo / Admin 四级 |

### 3.9 codex-mcp-server（MCP 服务器）

将 Codex 作为 MCP 服务器暴露，使其他 MCP 客户端可以将 Codex 用作工具：

- 通过 stdio 传输进行 JSON-RPC 通信
- 暴露 `codex` 工具：其他代理可通过 MCP 调用 Codex 执行编码任务
- 支持执行审批和补丁审批的 elicitation 流程

### 3.10 codex-config（配置系统）

基于 `config.toml` 的配置层栈：

| 配置来源 | 路径 |
|----------|------|
| 内置默认 | 编译时嵌入 |
| 用户配置 | `~/.codex/config.toml` |
| 项目配置 | 项目根目录 `.codex/config.toml` |
| 线程配置 | 会话内持久化设置 |
| 云配置 | 从 ChatGPT 后端拉取的配置约束 |

**可配置项**：模型选择、服务等级、审批策略、权限配置、沙箱模式、MCP 服务器、网络代理、功能开关、实时音频、Windows 沙箱级别、通知设置、主题、键位映射等。

---

## 四、扩展系统

### 4.1 扩展（Extensions）

位于 `ext/` 目录下，以独立 crate 形式实现的扩展功能：

| 扩展 | 功能 |
|------|------|
| `ext/extension-api` | 扩展 API 定义：ToolCallOutcome、扩展工具执行接口 |
| `ext/goal` | 长期目标扩展：代理可设置和跟踪跨轮次的目标 |
| `ext/guardian` | 守护者扩展：自动安全审查和审批决策 |
| `ext/image-generation` | 图像生成扩展：代理可调用 DALL-E 等生成图片 |
| `ext/memories` | 记忆扩展：代理可读写持久化记忆 |
| `ext/web-search` | 网络搜索扩展：代理可搜索互联网获取信息 |

### 4.2 连接器（Connectors）

连接器允许代理访问外部数据源（如代码仓库、文档、数据库等）。包含：
- 连接器目录缓存
- 连接器过滤和合并
- 连接器元数据管理
- 与 ChatGPT 账户体系集成

### 4.3 插件（Plugins）

插件系统位于 `core/src/plugins/`：
- 插件发现：扫描插件目录
- 插件注入：将插件指令注入模型上下文
- 插件提及解析：解析用户消息中的 `@plugin` 提及
- 可发现工具过滤：控制哪些插件工具向模型可见

---

## 五、代理执行流程

### 5.1 Turn（轮次）执行

一次完整的 Turn 流程：

```
用户输入 (Op::UserInput)
    │
    ▼
┌─ Session 接收 ─────────────────────────┐
│  1. 构建 TurnInput                      │
│     - 技能解析（显式/隐式提及）           │
│     - 插件解析                           │
│     - 连接器解析                         │
│     - MCP 工具暴露                      │
│     - 工具建议/搜索                     │
│  2. 运行 session_start 钩子             │
│  3. 构建模型上下文                       │
│     - 基础指令                           │
│     - 技能指令                           │
│     - 插件指令                           │
│     - 环境上下文                         │
│     - 工具定义列表                       │
└────────────────────────────────────────┘
    │
    ▼
┌─ 模型调用 (ModelClient) ───────────────┐
│  - 调用 OpenAI Responses API (SSE)      │
│  - 流式接收响应事件                      │
│  - 支持模型重新路由（Model Reroute）     │
│  - 支持自动重试                          │
└────────────────────────────────────────┘
    │
    ▼
┌─ 工具分发 (ToolRouter) ────────────────┐
│  1. 解析工具调用                         │
│  2. 运行 pre_tool_use 钩子              │
│  3. 执行策略检查（是否需要审批）          │
│  4. 工具执行（本地/MCP/扩展/动态）       │
│     - Shell 命令 → exec-server          │
│     - 代码补丁 → apply_patch            │
│     - MCP 工具 → MCP 服务器             │
│     - 动态工具 → 扩展 API               │
│  5. 运行 post_tool_use 钩子             │
│  6. 格式化输出 → 返回模型                │
└────────────────────────────────────────┘
    │
    ▼
┌─ 循环或终止 ────────────────────────────┐
│  - 模型继续调用工具 → 回到工具分发        │
│  - 模型返回最终答案 → TurnComplete       │
│  - 触发 turn_stop 钩子                  │
│  - 运行 after_agent 钩子                │
│  - 发送完成通知                         │
└────────────────────────────────────────┘
```

### 5.2 多代理系统（Multi-Agent）

Codex 支持多代理协作：
- **主代理**：接收用户请求，协调子代理
- **子代理**：执行特定子任务，向主代理报告
- **代理注册表**：按名称/角色注册和管理代理
- **深度限制**：防止子代理无限嵌套
- **线程生成**：每个子代理在独立线程中运行
- **代理间通信**：通过 `InterAgentCommunication` 操作传递消息

### 5.3 上下文压缩（Compaction）

当对话历史接近 token 限制时：

| 压缩方式 | 说明 |
|----------|------|
| **本地压缩** | 在客户端对历史进行摘要压缩 |
| **远程压缩 v1** | 调用模型 API 生成摘要 |
| **远程压缩 v2** | 更高效的远程压缩协议 |
| **自动压缩** | token 数超过阈值时自动触发 |
| **手动压缩** | 用户通过斜杠命令触发 |

### 5.4 审批系统

Codex 有三层审批机制：

1. **命令执行审批（ExecApproval）**：
   - 根据 `exec_policy` 判断哪些命令需要审批
   - 支持自动批准白名单（如 `ls`, `cat`）
   - 用户可决定：Approve / Reject / Amend

2. **代码补丁审批（PatchApproval）**：
   - 代理生成的代码修改需要用户确认
   - 展示 diff 供用户审查

3. **守护者自动审批（Guardian）**：
   - 基于风险评估自动审批低风险操作
   - 风险等级：Low / Medium / High
   - 可配置自动审批策略

---

## 六、模型提供商支持

Codex 支持多种模型提供商（通过 `codex-model-provider` 和 `codex-models-manager`）：

| 提供商 | 说明 |
|--------|------|
| **OpenAI** | 原生支持 Responses API（推荐） |
| **OpenRouter** | 通过 OpenRouter API 路由到多种模型 |
| **Ollama** | 本地 Ollama 部署 |
| **LMStudio** | 本地 LMStudio 部署 |
| **Gemini** | Google Gemini API |
| **DashScope** | 阿里通义千问 API |
| **Anthropic** | Claude API |
| **DeepSeek** | DeepSeek API |
| **xAI** | Grok API |

支持功能：
- 服务等级（service_tier）：flex / auto / default
- 推理力度（reasoning_effort）：low / medium / high
- 推理摘要（reasoning_summary）：concise / detailed
- 模型重新路由：后端可推荐更合适的模型
- 模型验证：部分模型需要额外账户验证

---

## 七、实时音频对话（Realtime）

Codex 支持实时语音交互：

- **传输方式**：WebSocket / WebRTC
- **音频输入**：麦克风录音（cpal 音频库）
- **音频输出**：扬声器播放（Linux 使用 cpal，macOS/Windows 使用平台特定实现）
- **语音选择**：20+ 种声音（Alloy, Ash, Echo, Shimmer 等）
- **文本回退**：也可通过文本输入实时对话
- **Token 预算**：实时对话有独立的 token 限制

---

## 八、会话管理

### 8.1 会话持久化

- **Rollout Recorder**：将每个 turn 的项目写入磁盘
- **Thread Store**：SQLite 数据库存储线程元数据
- **会话恢复**：可从历史会话恢复，保留完整上下文
- **会话归档**：旧会话自动归档到 `sessions/archived/`
- **Fork**：可从任意历史点 fork 新会话

### 8.2 会话历史管理

- 游标分页浏览历史会话列表
- 按名称/日期/状态搜索
- 会话元数据：模型、token 用量、创建时间等

---

## 九、安全特性

| 特性 | 说明 |
|------|------|
| **沙箱隔离** | Seatbelt / Bubblewrap+Landlock / Windows Sandbox |
| **进程加固** | 限制子进程能力（process-hardening） |
| **网络策略** | 可配置网络访问规则（允许/拒绝特定域名） |
| **执行策略** | 精细的命令级审批策略 |
| **守护者评估** | 自动风险评估和审批决策 |
| **密钥管理** | 通过 keyring-store 安全存储 API 密钥 |
| **认证** | 支持 ChatGPT 登录 / API Key / OAuth |

---

## 十、集成能力

### 10.1 IDE 集成

Codex 可通过 app-server 协议集成到 IDE：
- VS Code 扩展
- JetBrains 插件
- 其他支持 MCP 的编辑器

### 10.2 MCP 生态

- **作为 MCP 客户端**：连接外部 MCP 服务器，使用其工具
- **作为 MCP 服务器**：通过 `codex mcp-server` 被其他 MCP 客户端调用

### 10.3 Web 搜索

通过 `ext/web-search` 扩展，代理可以搜索互联网获取最新信息。

### 10.4 记忆系统

通过 `ext/memories` 扩展和 `memories/read`、`memories/write` crate，代理可以：
- 读取 `~/.codex/memories` 中的持久化记忆
- 写入新的记忆条目
- 记忆在跨会话间持久保留

---

## 十一、开发与构建

### 11.1 构建系统

- **Bazel**：主要生产构建系统，支持跨平台复现构建
- **Cargo**：本地开发构建，支持增量编译
- **just**：任务运行器（类似 make），封装常用操作

### 11.2 测试

| 测试类型 | 位置 |
|----------|------|
| 单元测试 | 各 crate 内的 `*_tests.rs` 文件 |
| 集成测试 | `core/suite/` 目录，使用 `test_codex` 设置端到端测试 |
| 快照测试 | 使用 `insta` 框架，特别是 TUI 渲染输出 |
| 测试支持 | `core_test_support`、`mcp_test_support`、`app_test_support` |

### 11.3 代码质量

- **Clippy 严格模式**：deny `expect_used`、`unwrap_used` 等
- **cargo-shear**：自动检测未使用的依赖
- **deny.toml**：许可证和安全性审查
- **codespell**：拼写检查
- **prettier**：非 Rust 文件格式化

---

## 十二、项目目录结构总结

```
codex/
├── codex-rs/                    # Rust 工作空间（核心）
│   ├── cli/                     # CLI 入口（codex 可执行文件）
│   ├── tui/                     # 终端用户界面
│   ├── core/                    # 核心业务逻辑（代理引擎）
│   ├── protocol/                # 内部协议定义（Op / EventMsg）
│   ├── tools/                   # 工具定义和执行
│   ├── sandboxing/              # 跨平台沙箱
│   ├── skills/                  # 技能系统
│   ├── core-skills/             # 核心技能实现
│   ├── codex-mcp/               # MCP 客户端管理
│   ├── mcp-server/              # MCP 服务器实现
│   ├── app-server/              # 应用服务器
│   ├── app-server-protocol/     # 服务器协议（v1/v2）
│   ├── app-server-transport/    # 传输层（UDS/stdio）
│   ├── app-server-client/       # 客户端 SDK
│   ├── app-server-daemon/       # 守护进程
│   ├── config/                  # 配置系统
│   ├── state/                   # 状态数据库（SQLite）
│   ├── connectors/              # 连接器系统
│   ├── exec/                    # 无头 CLI（自动化）
│   ├── exec-server/             # 命令执行服务器
│   ├── execpolicy/              # 执行策略
│   ├── execpolicy-legacy/       # 旧版执行策略
│   ├── prompts/                 # 提示词模板
│   ├── hooks/                   # 钩子系统
│   ├── login/                   # 认证管理
│   ├── keyring-store/           # 密钥存储
│   ├── feedback/                # 用户反馈
│   ├── features/                # 功能开关
│   ├── rollout/                 # 会话回放记录
│   ├── rollout-trace/           # 回放追踪
│   ├── message-history/         # 消息历史
│   ├── thread-store/            # 线程存储（SQLite）
│   ├── models-manager/          # 模型管理器
│   ├── model-provider/          # 模型提供商
│   ├── model-provider-info/     # 模型提供商信息
│   ├── responses-api-proxy/     # Responses API 代理
│   ├── codex-api/               # Codex API 客户端
│   ├── codex-client/            # Codex 客户端
│   ├── codex-backend-openapi-models/  # 后端 OpenAPI 模型
│   ├── realtime-webrtc/         # WebRTC 实时通信
│   ├── stdio-to-uds/            # stdio 到 UDS 桥接
│   ├── shell-command/           # Shell 命令解析
│   ├── shell-escalation/        # Shell 权限升级
│   ├── git-utils/               # Git 工具
│   ├── file-search/             # 文件搜索
│   ├── file-watcher/            # 文件监控
│   ├── file-system/             # 文件系统工具
│   ├── apply-patch/             # 代码补丁应用
│   ├── linux-sandbox/           # Linux 沙箱二进制
│   ├── windows-sandbox-rs/      # Windows 沙箱
│   ├── process-hardening/       # 进程加固
│   ├── network-proxy/           # 网络代理
│   ├── ollama/                  # Ollama 集成
│   ├── lmstudio/                # LMStudio 集成
│   ├── chatgpt/                 # ChatGPT 集成
│   ├── aws-auth/                # AWS 认证
│   ├── cloud-config/            # 云配置
│   ├── cloud-tasks*/            # 云端任务
│   ├── otel/                    # OpenTelemetry 遥测
│   ├── analytics/               # 分析事件
│   ├── agent-graph-store/       # 代理图存储
│   ├── agent-identity/          # 代理身份
│   ├── collaboration-mode-templates/  # 协作模式模板
│   ├── code-mode/               # 代码模式
│   ├── plugin/                  # 插件框架
│   ├── external-agent-migration/      # 外部代理迁移
│   ├── external-agent-sessions/       # 外部代理会话
│   ├── ext/                     # 扩展系统
│   │   ├── extension-api/       # 扩展 API
│   │   ├── goal/                # 目标扩展
│   │   ├── guardian/            # 守护者扩展
│   │   ├── image-generation/    # 图像生成扩展
│   │   ├── memories/            # 记忆扩展
│   │   └── web-search/          # 网络搜索扩展
│   ├── memories/                # 记忆系统
│   │   ├── read/                # 记忆读取
│   │   └── write/               # 记忆写入
│   ├── v8-poc/                  # V8 引擎概念验证
│   ├── uds/                     # Unix Domain Socket
│   ├── utils/                   # 工具库（20+ 个）
│   └── vendor/                  # 第三方依赖
├── codex-cli/                   # TypeScript CLI（旧版入口）
├── sdk/                         # SDK 封装
├── scripts/                     # 构建/维护脚本
├── docs/                        # 项目文档
├── patches/                     # 依赖补丁
└── third_party/                 # 第三方依赖
```

---

## 十三、技术亮点

1. **零依赖部署**：编译为单个静态链接二进制，无需运行时依赖
2. **跨平台**：macOS / Linux / Windows 全支持，各有优化
3. **可扩展的工具系统**：本地工具 + MCP 工具 + 扩展工具 + 动态工具
4. **安全优先**：多层沙箱 + 执行策略 + 守护者自动审查
5. **丰富的交互模式**：TUI / 无头 CLI / MCP 服务器 / IDE 集成 / 实时音频
6. **会话恢复与历史**：完整的会话持久化和恢复机制
7. **多代理协作**：支持主-子代理层次结构
8. **功能开关**：细粒度的功能启用/禁用控制
9. **配置层栈**：从内置默认到云配置的灵活配置叠加
10. **OpenTelemetry 集成**：完整的遥测和指标支持

---

## 十四、与 agentscope 的关系

本项目位于 `/Users/alex/Workshop/python/HiCoder/` 下，与 `agentscope/` 项目并列。`agentscope/` 是一个 Python 项目，看起来是另一个编码代理/框架实现。两者是独立的项目，Codex 是 OpenAI 的 Rust 实现编码代理，而 agentscope 是 Python 生态的代理框架。

---

*文档生成时间：2026-06-02*
*基于 codex 仓库最新 main 分支代码分析*
