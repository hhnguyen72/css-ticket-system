# Goals, Non-Goals, Constraints, Assumptions, and Measures of Success

## Goals

- Parse free-text CSS team requests and populate all six ticket fields with ≥ 90% field-level accuracy against a labeled ground-truth dataset.
- Redact every DoD ID number from source text before any ticket is output or stored, with zero leaked IDs across the evaluation set.

## Non-Goals

- The system only structures requests — it does not act on, route, assign, or close tickets.
- Redaction is limited to DoD IDs only; other PII classes (SSNs, passports, addresses) are out of scope.
- The system does not handle input delivery — ingestion from email, ticketing APIs, or shared drives is external.

## Constraints

- Unredacted DoD IDs must never appear in output fields — correctness here is non-negotiable due to regulatory and mission risk.
- Category must resolve to exactly one of three values: SEL/Commander's Request, Record Update, or Dissemination Info — no null, invented, or confidence-range outputs.

## Assumptions

- DoD ID numbers follow a known, consistent format reliably detectable by regex or a trained classifier.
- Incoming requests will generally include at least one email or phone number in the body text — no external directory lookup is expected.
- Every real request maps cleanly to exactly one category with no meaningful overlap or ambiguity in practice.

## Measures of Success

- Field-level extraction accuracy ≥90%, measured per field per ticket against a labeled ground-truth set, with results reported separately per field
- DoD ID redaction recall = 100% across the evaluation set — treated as a hard pass/fail gate, not averaged into the accuracy score.