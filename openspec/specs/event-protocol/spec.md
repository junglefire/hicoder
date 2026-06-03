## ADDED Requirements

### Requirement: TextDelta event
The system SHALL emit a TextDelta event for each incremental text chunk received from the model. TextDelta SHALL contain a `text` field with the delta content.

#### Scenario: Single text chunk
- **WHEN** the model returns a chunk with text "Hello"
- **THEN** a TextDelta event is yielded with text="Hello"

#### Scenario: Multiple text chunks concatenated
- **WHEN** the model returns sequential chunks ["Hello", " ", "world"]
- **THEN** three TextDelta events are yielded that concatenate to "Hello world"

### Requirement: ToolCall event
The system SHALL emit a ToolCall event when the model requests a tool invocation. ToolCall SHALL contain `id` (str), `name` (str), and `arguments` (str) fields.

#### Scenario: Single tool call
- **WHEN** the model calls a tool named "shell" with arguments {"command": "ls"}
- **THEN** a ToolCall event is yielded with id, name="shell", and arguments='{"command": "ls"}'

#### Scenario: Multiple parallel tool calls
- **WHEN** the model calls two tools simultaneously
- **THEN** two ToolCall events are yielded, each with a unique id

### Requirement: ToolCallDone event
The system SHALL emit a ToolCallDone event when the model finishes providing all arguments for a specific tool call. ToolCallDone SHALL contain `id`, `name`, and `arguments` fields matching the corresponding ToolCall event.

#### Scenario: Tool call arguments complete
- **WHEN** the model finishes streaming arguments for tool call id "call_1"
- **THEN** a ToolCallDone event is yielded with id="call_1"

### Requirement: TurnComplete event
The system SHALL emit a TurnComplete event when the model finishes a complete turn (no more tool calls pending). TurnComplete SHALL contain `usage` (TokenUsage) with prompt_tokens, completion_tokens, and total_tokens fields.

#### Scenario: Turn completes with usage
- **WHEN** the model finishes responding
- **THEN** a TurnComplete event is yielded with usage containing token counts

### Requirement: Error event
The system SHALL emit an Error event when a model call fails. Error SHALL contain a `message` (str) field describing the failure.

#### Scenario: API returns error
- **WHEN** the model API returns a 400 error
- **THEN** an Error event is yielded with a message describing the error

#### Scenario: Network timeout
- **WHEN** the model connection times out after all retries
- **THEN** an Error event is yielded with a timeout message
