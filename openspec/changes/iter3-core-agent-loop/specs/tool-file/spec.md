## ADDED Requirements

### Requirement: File read (read_file)
The system SHALL provide a `read_file` tool that reads a file and returns its content. The tool SHALL support line-range parameters and enforce a maximum output size (default: 20000 bytes). Large files SHALL be truncated with a notice.

#### Scenario: Read small file
- **WHEN** read_file is called on a 500-byte file
- **THEN** the full file content is returned

#### Scenario: Read large file with truncation
- **WHEN** read_file is called on a file exceeding the maximum output size
- **THEN** the content is truncated at the limit with a "[truncated]" notice appended

#### Scenario: File not found
- **WHEN** read_file is called on a non-existent file
- **THEN** an error message is returned indicating the file does not exist

### Requirement: File write (write_file)
The system SHALL provide a `write_file` tool that writes content to a file, creating the file and any missing parent directories. The tool SHALL require absolute paths and reject paths outside the working directory.

#### Scenario: Write new file
- **WHEN** write_file is called with a path and content
- **THEN** the file is created with the specified content

#### Scenario: Write creates parent directories
- **WHEN** write_file is called with a path whose parent directories do not exist
- **THEN** parent directories are created and the file is written

#### Scenario: Path outside working directory rejected
- **WHEN** write_file is called with a path above the working directory
- **THEN** an error is returned and no file is written

### Requirement: File edit (edit_file)
The system SHALL provide an `edit_file` tool that performs exact string replacement in a file. The tool SHALL require both `old_string` and `new_string` parameters. If `old_string` is not found or appears multiple times, the tool SHALL return an error.

#### Scenario: Successful single replacement
- **WHEN** edit_file is called with old_string that appears exactly once
- **THEN** the old_string is replaced with new_string in the file

#### Scenario: old_string not found
- **WHEN** edit_file is called with old_string that does not exist in the file
- **THEN** an error is returned indicating the string was not found

#### Scenario: old_string appears multiple times
- **WHEN** edit_file is called with old_string that appears more than once
- **THEN** an error is returned indicating the string is ambiguous
