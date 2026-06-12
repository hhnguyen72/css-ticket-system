# Acceptance Criteria

## AC-001 — Happy Path: High-Confidence Classification
**Given** a structured form submission with all five fields populated,
**When** the submission is processed by the tool,
**Then** all five fields are present in the output payload with ≥90% field-level accuracy and no field is silently omitted.


## AC-002 — Low-Confidence Fallback: Review Flag. 
**Given** a batch of tickets with mixed priority tiers and Need By Dates,
**When**  the tool processes and returns the batch,
**Then** tickets are sorted priority tier ascending (1 → 3), ties within the same tier are broken by Need By Date ascending, and no ticket is omitted from the sorted output.


## AC-003 — Accuracy Validation: Batch Correctness. System meets accuracy standard across a verified ticket set
**Given** a submitted ticket containing one or more 10-digit DoD ID numbers anywhere in the form fields,
**When** the tool processes the submission,
**Then** every DoD ID is replaced with [DOD_ID_REDACTED] before output, non-DoD numeric strings are left unchanged, and redaction achieves 100% coverage across all test submissions.

## AC-004 — PII Redaction: Data Protection Before Storage. Personal information is redacted before any data is logged or stored
**Given** a CSS ticket contains personally identifiable information
**When** the ticket is processed for categorization
**Then** all personally identifiable fields are redacted before the ticket is logged or stored and the category assigned to the ticket is not affected by the redaction
