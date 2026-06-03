## ADDED Requirements

### Requirement: Model creation from Config
The system SHALL create an AgentScope model instance from a loaded Config, mapping provider to the corresponding AgentScope model class (openai → OpenAIChatModel, anthropic → AnthropicChatModel) and injecting the resolved API key via Credential.

#### Scenario: OpenAI model creation
- **WHEN** Config has provider="openai", model="gpt-4o", and a resolved api_key
- **THEN** an OpenAIChatModel instance is created with the correct credential and model name

#### Scenario: Anthropic model creation
- **WHEN** Config has provider="anthropic", model="claude-sonnet-4-20250514", and a resolved api_key
- **THEN** an AnthropicChatModel instance is created with the correct credential and model name

#### Scenario: Missing API key raises error
- **WHEN** Config has no api_key and no matching environment variable
- **THEN** a descriptive error is raised before attempting model creation

### Requirement: Model parameter control
The system SHALL support configuring temperature, max_tokens, top_p, and reasoning_effort parameters on the model instance. Parameters SHALL be passed to AgentScope's Parameters model during initialization.

#### Scenario: Custom temperature applied
- **WHEN** temperature=0.7 is configured
- **THEN** the model instance uses temperature=0.7 for all calls

#### Scenario: Default parameters applied
- **WHEN** no custom parameters are configured
- **THEN** the model uses sensible defaults (temperature=1.0, max_tokens=4096)

### Requirement: Streamed model calls
The model client SHALL call the underlying API with stream=True enabled. The client SHALL yield AgentEvent objects as chunks arrive, not wait for the complete response.

#### Scenario: Streaming text response
- **WHEN** the model returns a text-only response
- **THEN** the client yields TextDelta events as each chunk arrives, followed by a TurnComplete event

#### Scenario: Streaming response with tool calls
- **WHEN** the model returns tool calls in its response
- **THEN** the client yields ToolCall events with id, name, and arguments, followed by TurnComplete

### Requirement: Retry and fault tolerance
The system SHALL retry failed API calls up to 3 times with a configurable delay between attempts. Retry SHALL only apply to retryable exceptions (network errors, 429, 500-series). Non-retryable errors (400, auth failure) SHALL raise immediately.

#### Scenario: Transient network error retried
- **WHEN** a network timeout occurs on the first attempt
- **THEN** the call is retried up to 3 times with delay between attempts

#### Scenario: Auth error not retried
- **WHEN** the API returns a 401 Unauthorized error
- **THEN** the error is raised immediately without retry

### Requirement: Token usage tracking
The system SHALL extract and expose token usage information (prompt tokens, completion tokens, total tokens) from the final model response. Token usage SHALL be attached to the TurnComplete event.

#### Scenario: Usage included in response
- **WHEN** a model call completes successfully
- **THEN** the TurnComplete event contains usage with prompt_tokens, completion_tokens, and total_tokens
