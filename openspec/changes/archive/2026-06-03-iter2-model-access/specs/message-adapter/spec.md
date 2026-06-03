## ADDED Requirements

### Requirement: User message to AgentScope Msg conversion
The system SHALL convert HiCoder user messages (role + content format) to AgentScope `Msg` objects before sending to the model.

#### Scenario: Simple user message conversion
- **WHEN** converting a user message with content "fix the bug in app.py"
- **THEN** an AgentScope Msg is created with role="user" and the correct content blocks

#### Scenario: Multi-turn conversation conversion
- **WHEN** converting a conversation history with alternating user/assistant messages
- **THEN** each message is converted to the corresponding AgentScope Msg with correct role and content

### Requirement: Assistant response to internal format conversion
The system SHALL convert AgentScope `ChatResponse` content blocks to HiCoder AgentEvent objects. TextBlock content SHALL become TextDelta events. ToolCallBlock content SHALL become ToolCall events.

#### Scenario: Text response conversion
- **WHEN** AgentScope returns a ChatResponse with TextBlock content
- **THEN** the content is emitted as TextDelta events

#### Scenario: Tool call response conversion
- **WHEN** AgentScope returns a ChatResponse with ToolCallBlock content
- **THEN** the content is emitted as ToolCall events with parsed id, name, and arguments

### Requirement: Tool result message creation
The system SHALL create AgentScope-compatible messages containing tool execution results, for inclusion in the next model call. Tool result messages SHALL have role "tool" and include the tool call id and output content.

#### Scenario: Tool result appended
- **WHEN** a shell command exits with code 0 and stdout="file1\nfile2\n"
- **THEN** a tool result message is created with the tool call id and the output text
