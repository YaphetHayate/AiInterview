## ADDED Requirements

### Requirement: Section-based log output format
The system SHALL output log entries using a section-based format with Unicode box-drawing separators. Each section SHALL contain a timestamp header, a tag line enclosed in `╔═╗`/`╚═╝` borders, and the full content below without truncation.

#### Scenario: Single log section output
- **WHEN** `_log_section(logger, "[MANAGER] Output", content="...")` is called
- **THEN** the log file SHALL contain a timestamp line, a separator line with `╔` and `║`, the tag text, a closing separator with `╚`, and the full content on subsequent lines

#### Scenario: Content exceeds 300 characters
- **WHEN** logged content is longer than 300 characters
- **THEN** the system SHALL output the complete content without any truncation

### Requirement: Manager System Prompt logging on session start
The system SHALL log the Manager agent's full system prompt exactly once at the beginning of each interview session, in `start_dual_interview`.

#### Scenario: New interview session starts
- **WHEN** `start_dual_interview` is called
- **THEN** the system SHALL write a log section with tag `[MANAGER] System Prompt` containing the complete text of `MANAGER_SYSTEM_PROMPT`

#### Scenario: Subsequent chat rounds
- **WHEN** `dual_interview_chat` is called for an existing session
- **THEN** the system SHALL NOT log the Manager System Prompt again

### Requirement: Manager input and output logging
The system SHALL log the complete input message and raw output for every Manager agent invocation, without truncation.

#### Scenario: Manager receives input
- **WHEN** the Manager agent is invoked with a message
- **THEN** the system SHALL write a log section with tag `[MANAGER] Input (source=...)` containing the complete input message

#### Scenario: Manager produces output
- **WHEN** the Manager agent returns a response
- **THEN** the system SHALL write a log section with tag `[MANAGER] Output` containing the complete raw response text

### Requirement: Interviewer prompt and response logging
The system SHALL log the Interviewer agent's system prompt and user message as separate sections, followed by its response.

#### Scenario: Interviewer system prompt
- **WHEN** the Interviewer agent is invoked
- **THEN** the system SHALL write a log section with tag `[INTERVIEWER] System Prompt` containing the complete system prompt

#### Scenario: Interviewer user message
- **WHEN** the Interviewer agent is invoked
- **THEN** the system SHALL write a log section with tag `[INTERVIEWER] User Message` containing the complete user message

#### Scenario: Interviewer response
- **WHEN** the Interviewer agent returns a response
- **THEN** the system SHALL write a log section with tag `[INTERVIEWER] Response` containing the complete response text

### Requirement: Flow event logging
The system SHALL log flow control events (PENDING_BUFFER, FORCE_COMPLETE, STAGE_ADVANCE, AWAIT_CONTINUATION) with tag prefix `[FLOW]` and concise descriptive content.

#### Scenario: Candidate answer buffered
- **WHEN** a candidate message is added to the pending buffer
- **THEN** the system SHALL write a log section with tag `[FLOW] Pending Buffer` containing the buffer count and accumulated text

#### Scenario: Stage advancement
- **WHEN** the interview advances to a new stage
- **THEN** the system SHALL write a log section with tag `[FLOW] Stage Advance` containing the from/to stage numbers

### Requirement: Removal of old log function and MANAGER_PARSED
The system SHALL remove the `_log()` function and all `MANAGER_PARSED` log entries. No parsed JSON output SHALL be logged separately from the raw Manager output.

#### Scenario: Old _log function removed
- **WHEN** the codebase is refactored
- **THEN** the `_log()` function SHALL NOT exist and no code SHALL reference it

#### Scenario: Manager parsed output
- **WHEN** the Manager response is parsed
- **THEN** the system SHALL NOT write a separate `MANAGER_PARSED` log entry
