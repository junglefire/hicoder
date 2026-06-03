## ADDED Requirements

### Requirement: Agent Turn loop
The system SHALL provide an asynchronous generator `agent_loop()` that executes a complete agent turn: build context → call model → parse tool calls → execute tools → return results → repeat until no tool calls remain. The generator SHALL yield AgentScope's AgentEvent objects (TEXT_BLOCK_DELTA, TOOL_CALL_START/DELTA/END, TOOL_RESULT_*, MODEL_CALL_START/END, etc.) directly, plus HiCoder-defined Error and TurnComplete events.

#### Scenario: Simple text response with no tools
- **WHEN** the model responds with text only, no tool calls
- **THEN** the loop yields TextBlockDelta events and then TurnComplete, then stops

#### Scenario: Tool call followed by text
- **WHEN** the model calls one tool and provides text
- **THEN** the loop yields TextBlockDelta and ToolCall events, executes the tool, yields ToolResult events, calls model again, and continues until no tool calls remain

#### Scenario: Multiple tool calls in parallel
- **WHEN** the model calls three tools in one response
- **THEN** all three tools execute concurrently, results are returned to the model in a single follow-up call

#### Scenario: Error during tool execution
- **WHEN** a tool execution raises an exception
- **THEN** the loop yields an Error event and continues, passing the error text as the tool result to the model

### Requirement: Maximum turn limit
The agent loop SHALL enforce a maximum number of model calls per user message (default: 50). When the limit is reached, the loop SHALL yield an Error event and stop.

#### Scenario: Turn limit reached
- **WHEN** the model keeps calling tools for 50 consecutive turns
- **THEN** the loop yields an Error("Maximum turns reached") event and stops

### Requirement: Cancellation support
The agent loop SHALL support cancellation via an asyncio.Event. When the event is set, the loop SHALL stop after the current turn completes and yield an Error event.

#### Scenario: User cancels mid-turn
- **WHEN** the user triggers cancellation during model response or tool execution
- **THEN** the loop stops at the end of the current turn and yields an Error("Cancelled") event

### Requirement: Retry with exponential backoff
The agent loop SHALL retry transient errors (network timeout, rate limit, 5xx) with exponential backoff (initial delay: 1s, max delay: 30s, max retries: 3). Non-retryable errors (invalid API key, model not found) SHALL immediately yield an Error event and stop.

#### Scenario: Transient network error
- **WHEN** the model call fails with a connection timeout
- **THEN** the loop waits 1s, retries, and succeeds on the second attempt

#### Scenario: Max retries exceeded
- **WHEN** a transient error persists across 3 retries
- **THEN** the loop yields an Error event and stops

#### Scenario: Non-retryable error
- **WHEN** the model call fails with an invalid API key
- **THEN** the loop immediately yields an Error event without retrying

### Requirement: Pending input queue
The agent loop SHALL support a pending input queue (asyncio.Queue) that allows new user messages to be enqueued during an ongoing turn. Between each model call, the loop SHALL drain pending inputs and append them to the conversation history.

#### Scenario: User sends message during tool execution
- **WHEN** the user sends a new message while tools are executing
- **THEN** the message is enqueued and appended to history before the next model call

#### Scenario: Empty queue between turns
- **WHEN** no pending messages exist between model calls
- **THEN** the loop proceeds normally without blocking

### Requirement: Token usage tracking
Each MODEL_CALL_END event SHALL include input_tokens and output_tokens counts from the model response. The agent loop SHALL accumulate total token usage across all turns and include it in the TurnComplete event.

#### Scenario: Single model call
- **WHEN** the model responds with 100 input tokens and 50 output tokens
- **THEN** the MODEL_CALL_END event contains input_tokens=100, output_tokens=50

#### Scenario: Multiple turns accumulate usage
- **WHEN** three model calls produce (100, 50), (200, 80), (150, 60) tokens
- **THEN** the TurnComplete event contains total_input_tokens=450, total_output_tokens=190
