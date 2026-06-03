## ADDED Requirements

### Requirement: Shell command execution
The system SHALL provide a `shell` tool that executes a shell command via `asyncio.create_subprocess_exec` and returns stdout, stderr, and exit code. The tool SHALL enforce a configurable timeout (default: 30 seconds).

#### Scenario: Successful command execution
- **WHEN** shell tool executes `echo "hello"` with default timeout
- **THEN** the result contains stdout "hello\n", empty stderr, and exit_code=0

#### Scenario: Command with stderr
- **WHEN** shell tool executes a command that writes to stderr
- **THEN** the result captures stderr content separately from stdout

#### Scenario: Command timeout
- **WHEN** a command runs longer than the configured timeout
- **THEN** the process is killed and an error result is returned with a timeout message

#### Scenario: Command not found
- **WHEN** the command does not exist
- **THEN** the result contains stderr with "command not found" and a non-zero exit code

### Requirement: Working directory constraint
The shell tool SHALL execute commands within the session's configured working directory (cwd). The tool SHALL not allow changing directory above the project root.

#### Scenario: Command runs in project directory
- **WHEN** shell executes `pwd` with cwd set to /Users/alex/project
- **THEN** the stdout shows /Users/alex/project
