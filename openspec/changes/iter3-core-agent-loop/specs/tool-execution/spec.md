## ADDED Requirements

### Requirement: Tool registration and discovery
The system SHALL provide a ToolRegistry that discovers and registers tools decorated with `@tool`. The registry SHALL automatically generate OpenAI-compatible JSON Schema tool definitions from the tool function's signature and docstring.

#### Scenario: Auto-discovery of decorated tools
- **WHEN** the registry is initialized
- **THEN** all tools registered via `@tool` decorator are available in the registry

#### Scenario: Generate tool definitions
- **WHEN** registry.get_tool_definitions() is called
- **THEN** a list of JSON Schema tool definitions is returned, compatible with OpenAI function calling format

### Requirement: Tool execution
The registry SHALL execute a named tool with given arguments and return the result. The execution SHALL be asynchronous and support timeout.

#### Scenario: Execute registered tool
- **WHEN** registry.execute("shell", {"command": "echo hello"}) is called
- **THEN** the shell tool runs and returns its result

#### Scenario: Unknown tool raises error
- **WHEN** registry.execute("nonexistent_tool", {}) is called
- **THEN** a ValueError is raised with the tool name in the error message

### Requirement: Parallel tool execution
The system SHALL support concurrent execution of multiple tool calls using asyncio.gather. Each tool call executes independently; the caller receives all results when all complete.

#### Scenario: Three tools execute in parallel
- **WHEN** three tool calls are submitted to parallel_execute()
- **THEN** all three run concurrently and results are returned when all complete

### Requirement: Turn diff tracking
The system SHALL track file modifications during a turn. When write_file or edit_file successfully modifies a file, the system SHALL record the change and emit a unified diff event. The diff SHALL include the file path, old content hash, and new content hash.

#### Scenario: edit_file produces diff
- **WHEN** edit_file replaces "hello" with "world" in file.py
- **THEN** a diff event is emitted with the unified diff of the change

#### Scenario: write_file produces diff
- **WHEN** write_file creates or overwrites a file
- **THEN** a diff event is emitted with the full file content as the diff
