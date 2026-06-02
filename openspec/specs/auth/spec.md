# auth Specification

## Purpose
TBD - created by archiving change iter1-skeleton-config. Update Purpose after archive.
## Requirements
### Requirement: API Key from environment variable
The system SHALL read API Key from environment variables: `OPENAI_API_KEY` for openai provider, `ANTHROPIC_API_KEY` for anthropic provider. Environment variable values SHALL take precedence over config file values. The resolved key SHALL be used to construct AgentScope `OpenAICredential` or `AnthropicCredential` instances.

#### Scenario: OPENAI_API_KEY is set
- **WHEN** the provider is "openai" and `OPENAI_API_KEY` is set in the environment
- **THEN** the resolved api_key equals the environment variable value

#### Scenario: Environment overrides config file
- **WHEN** config.toml contains `api_key = "key-from-file"` but `OPENAI_API_KEY="key-from-env"` is set
- **THEN** the resolved api_key equals "key-from-env"

### Requirement: API Key from config file fallback
When the corresponding environment variable is not set, the system SHALL fall back to reading `api_key` from the loaded config file.

#### Scenario: No env var, config file has key
- **WHEN** `OPENAI_API_KEY` is not set and config.toml has `api_key = "sk-..."`
- **THEN** the resolved api_key equals "sk-..."

### Requirement: Missing API Key error
When no API Key is found from either environment or config file, the system SHALL raise a clear error message indicating which environment variable to set (e.g., `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) and the config file path to add the key to.

#### Scenario: No API key anywhere
- **WHEN** provider is "openai" and neither `OPENAI_API_KEY` nor config `api_key` is set
- **THEN** a descriptive error is raised mentioning `OPENAI_API_KEY` and the config file path

### Requirement: Provider-specific key resolution
The system SHALL resolve the API Key based on the configured provider: openai → `OPENAI_API_KEY`, anthropic → `ANTHROPIC_API_KEY`.

#### Scenario: Anthropic provider
- **WHEN** provider is "anthropic" and `ANTHROPIC_API_KEY` is set
- **THEN** the resolved api_key equals the `ANTHROPIC_API_KEY` value

