# Requirements — EARS Syntax (Need Review)

## Ubiquitous Requirements 
**REQ-U-001**
The system shall extract all six fields (category, priority, timeline, description, poc_emails[], poc_phones[]) with a per-field confidence score (0.00–1.00) on every CSS request received. If a field cannot be extracted, the system shall return null and conf:0.00 — fabrication is never permitted.

**REQ-U-002**
The system shall scan the full input text of every ticket for DoD ID patterns — defined as exactly 10 consecutive decimal digits (\b\d{10}\b) not preceded or followed by additional digits — and replace each match with [DOD_ID_REDACTED] across all output fields before the ticket is returned or stored. No ticket in which the source text contained an unredacted DoD ID shall be emitted, regardless of field, context, or confidence level.

**REQ-U-003**
The system shall assign exactly one category value — SEL/Commander's Request, Record Update, or Dissemination Info — to every processed ticket. category:null is never a valid output. When evaluated against a labeled ground-truth corpus of ≥100 CSS requests, the system shall achieve ≥90% exact-match accuracy on the category field, reported per-category.

## Event-Driven Requirements

**REQ-E-001**
When a CSS request is received, the system shall parse and return all six structured fields with per-field confidence scores in the response payload.

**REQ-E-002**
When classification confidence for all three categories falls below 0.60, the system shall set category_flag:"REVIEW_REQUIRED" alongside the best-guess category. Silently defaulting to any fixed category without setting this flag is a violation.


## Unwanted-Behaviour Requirements

**REQ-IF-001**
If a field cannot be extracted from the input, the system shall never infer, default, or fabricate a value. The output for that field shall be null with conf:0.00. Outputting a non-null value with no extractable signal in the source text is a violation.

**REQ-IF-002**
If a 10-digit numeric string matching the DoD ID pattern is present anywhere in the source text, the system shall not leave it unredacted in any output field. The match is format-based — surrounding labels such as "Ref#" or "ID:" do not exempt a string from redaction.

**REQ-IF-003**
If classification confidence is below threshold and category_flag:"REVIEW_REQUIRED" is not set, the system shall not emit the ticket. Outputting a category with sub-threshold confidence and no review flag is an explicit violation.

## Optional Feature Requirements

**REQ-W-001**
Where strict extraction mode is enabled, the system shall reject any parsed ticket in which category, description, or priority is null, returning an error response to the caller rather than passing the incomplete ticket downstream.

**REQ-W-002**
Where the redaction audit feature is enabled, the system shall write a log entry for each redaction event recording the ticket ID, pattern match count, affected field names, and timestamp — but never the original unredacted value.

**REQ-W-003**
Where the configurable threshold feature is enabled, the system shall use the operator-supplied confidence value (range 0.01–0.99) as the REVIEW_REQUIRED trigger in place of the default 0.60. The system shall reject configuration values outside that range at startup.

## State-Driven Requirements

**REQ-WH-001**
While a ticket's category_flag is REVIEW_REQUIRED, the system shall block the ticket from downstream routing, assignment, or storage in any final state until an authorized reviewer confirms or overrides the category.

**REQ-WH-002**
While a ticket is in the output preparation stage, the system shall hold the response and complete a full redaction pass across all fields before releasing the payload. No partial or unscanned output shall be emitted.

**REQ-WH-003**
While a parsed ticket contains null values for three or more required fields, the system shall route the ticket to a manual review queue and suppress automated processing until an authorized operator acknowledges the incomplete record.