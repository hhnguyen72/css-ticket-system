# Acceptance Criteria

## AC-001 — Happy Path: High-Confidence Classification. Ticket is confidently categorized without review
**Given** a CSS ticket has been submitted for processing
**When** the classifier returns a confidence score at or above the threshold for any category
**Then** the ticket is assigned exactly one of the following categories:
      | SEL/Commander's Request |
      | Record Update           |
      | Dissemination Info      |
    And the category field is never left blank
    And the ticket is not flagged for manual review

## AC-002 — Low-Confidence Fallback: Review Flag. Ticket is flagged for review when confidence is insufficient
**Given** a CSS ticket has been submitted for processing
**When** the classifier returns a confidence score below the threshold for all categories
**Then** the ticket is assigned the best available category
    And the ticket is flagged for manual review
    And the category field is never left blank

## AC-003 — Accuracy Validation: Batch Correctness. System meets accuracy standard across a verified ticket set
**Given** a set of CSS tickets with pre-verified correct category labels exists
**When** the system processes that set of tickets
**Then** the system's category assignments must match the verified labels at least nine times out of ten
    And accuracy results are reported separately for each category

## AC-004 — PII Redaction: Data Protection Before Storage. Personal information is redacted before any data is logged or stored
**Given** a CSS ticket contains personally identifiable information
**When** the ticket is processed for categorization
**Then** all personally identifiable fields are redacted before the ticket is logged or stored
    And the category assigned to the ticket is not affected by the redaction
