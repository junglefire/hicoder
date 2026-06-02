## ADDED Requirements

### Requirement: Three-layer config loading
The system SHALL load configuration from three layers in order: built-in defaults → user config (`~/.hicoder/config.toml`) → project config (`.hicoder/config.toml`). Values from later layers SHALL override earlier layers for non-None fields.

#### Scenario: All three layers present
- **WHEN** all three config layers exist with overlapping fields
- **THEN** the final Config object reflects project config values where set, falling back to user config, then built-in defaults

#### Scenario: Only built-in defaults exist
- **WHEN** no user or project config file exists
- **THEN** the system returns built-in default values without error

#### Scenario: User config overrides defaults
- **WHEN** user config.toml sets `model = "claude-sonnet-4-20250514"` and built-in default is `model = "gpt-4o"`
- **THEN** the loaded Config has `model = "claude-sonnet-4-20250514"`

### Requirement: Config data structure
The Config object SHALL contain at minimum: `model` (str), `provider` (Literal["openai", "anthropic"]), `api_key` (str | None), `approval_policy` (str), `sandbox_mode` (str), `cwd` (Path), `hicoder_home` (Path), `max_tokens` (int). The Config SHALL be compatible with AgentScope's model initialization (provider + model name map to AgentScope model classes).

#### Scenario: Config validates provider value
- **WHEN** a config file specifies `provider = "invalid"`
- **THEN** a validation error is raised listing valid values: "openai", "anthropic"

#### Scenario: Config uses sensible defaults
- **WHEN** no config file is provided
- **THEN** default model is "gpt-4o", provider is "openai", max_tokens is 4096

### Requirement: Built-in default config file
The package SHALL include a `default.toml` file in the `config/` directory containing all default configuration values.

#### Scenario: default.toml is loadable
- **WHEN** the system reads the bundled `default.toml`
- **THEN** it parses without error and produces a valid Config object

### Requirement: Custom config file path
The system SHALL accept an optional custom config file path that replaces the project config layer.

#### Scenario: Custom config path specified
- **WHEN** a custom path `/tmp/my-config.toml` is provided
- **THEN** that file is used as the project config layer instead of `.hicoder/config.toml`
