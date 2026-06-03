## ADDED Requirements

### Requirement: Context assembly
The system SHALL build model input by assembling: system prompt (built-in), AGENTS.md project instructions (if available), tool definitions (as JSON Schema in the `tools` parameter), and conversation history (ordered list of user/assistant/tool messages).

#### Scenario: Full context with project instructions
- **WHEN** a project directory with AGENTS.md is specified
- **THEN** the AGENTS.md content is included as part of the system message content

#### Scenario: No project directory specified
- **WHEN** no project directory is provided
- **THEN** only the built-in system prompt is used as the system message

### Requirement: System prompt generation
The system SHALL generate a system prompt that includes: agent identity and role, available tools overview, AGENTS.md content (if present), and behavioral guidelines. The system prompt SHALL be included as a single SystemMsg at the start of every model call.

#### Scenario: System prompt includes tool descriptions
- **WHEN** the context is built with 4 registered tools
- **THEN** the system prompt includes a summary of each tool's name and purpose
