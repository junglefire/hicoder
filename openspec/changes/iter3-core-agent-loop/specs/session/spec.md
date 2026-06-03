## ADDED Requirements

### Requirement: Session lifecycle management
The system SHALL provide a Session class that manages the conversation lifecycle. The Session SHALL maintain: message history (list of AgentMessage), tool registry (ToolRegistry), loaded Config, and project directory path.

#### Scenario: Session initialization
- **WHEN** a Session is created with a Config and optional project_dir
- **THEN** the Session initializes with empty message history, populated tool registry, and stores config and project_dir

#### Scenario: Session adds user message
- **WHEN** Session.receive_user_message("hello") is called
- **THEN** the message is appended to the Session's message history

### Requirement: Message history access
The Session SHALL provide access to the complete message history for context building. The history SHALL include system, user, assistant, and tool role messages in chronological order.

#### Scenario: History grows with turns
- **WHEN** a user sends two messages and the model responds to each
- **THEN** the Session history contains: user_msg_1, assistant_msg_1, user_msg_2, assistant_msg_2

### Requirement: Tool result formatting
The Session SHALL format tool execution results as AgentMessage objects with role="tool", content containing stdout/stderr/exit_code information, and tool_call_id linking to the original tool call.

#### Scenario: Successful tool result
- **WHEN** a shell command exits with code 0
- **THEN** the tool result message contains the stdout text and exit_code=0

#### Scenario: Failed tool result
- **WHEN** a shell command exits with non-zero code
- **THEN** the tool result message contains stderr text and the non-zero exit_code
