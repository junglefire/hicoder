## MODIFIED Requirements

### Requirement: Tool parameter support
The `stream()` method of ModelClient SHALL accept an optional `tools` parameter: a list of JSON Schema tool definitions. When provided, the tools SHALL be passed to the underlying AgentScope model call, enabling function calling.

#### Scenario: Stream with tool definitions
- **WHEN** stream() is called with a list of tool definitions
- **THEN** the model is invoked with those tools available for function calling

#### Scenario: Stream without tools
- **WHEN** stream() is called with tools=None
- **THEN** the model is invoked without tool definitions (text-only mode)
