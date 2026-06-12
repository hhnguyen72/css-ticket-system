# Requirements — EARS Syntax (Need Review)

## Ubiquitous Requirements 
**REQ-U-001**
The system shall extract all six fields (category, priority, timeline, description, poc_emails[], poc_phones[]) with a per-field confidence score (0.00–1.00) on every CSS request received. If a field cannot be extracted, the system shall return null and conf:0.00 — fabrication is never permitted.

**REQ-U-002**
The system shall sort all tickets in a batch by priority tier ascending (1 → 3), breaking ties within the same tier by Need By Date ascending, and shall return all tickets in the resolved order with no ticket omitted from the sorted output.


## Event-Driven Requirements

**REQ-E-001**
When a structured form submission is received, the system shall extract all five required fields — category, priority, timeline, description, and POC — and return a fully populated ticket payload within 5 seconds.

**REQ-E-002**
When a 10-digit numeric string matching \b\d{10}\b is detected in any field of a submitted form, the system shall replace it with [DOD_ID_REDACTED] before the ticket is written to storage or surfaced in any output.


## Unwanted-Behaviour Requirements

**REQ-IF-001**
If a submitted form contains a category value that does not map to any of the three canonical categories — SEL/Commander's Signature, Record Update, or Dissemination Info — the system shall reject the ticket, return a descriptive validation error to the submitter, and shall not create a partial or uncategorized ticket record in the system.


## Optional Feature Requirements

**REQ-W-001**
Where strict extraction mode is enabled, the system shall reject any parsed ticket in which category, description, or priority is null, returning an error response to the caller rather than passing the incomplete ticket downstream.

**REQ-W-002**
Where the redaction audit feature is enabled, the system shall write a log entry for each redaction event recording the ticket ID, pattern match count, affected field names, and timestamp — but never the original unredacted value.

**REQ-W-003**
Where the configurable threshold feature is enabled, the system shall use the operator-supplied confidence value (range 0.01–0.99) as the REVIEW_REQUIRED trigger in place of the default 0.60. The system shall reject configuration values outside that range at startup.

## State-Driven Requirements

**REQ-WH-001**
While one or more Priority 1 (SEL/Commander's Signature) tickets remain unresolved in the queue, the system shall maintain those tickets at the top of the sorted ticket list regardless of the Need By Date of any lower-priority tickets.
